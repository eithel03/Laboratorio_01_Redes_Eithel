#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import getpass
import json
import os
from datetime import datetime

import yaml

from netmiko import ConnectHandler
from netmiko.exceptions import (
    NetmikoTimeoutException,
    NetmikoAuthenticationException
)


# ==========================================================
# COMANDOS POR TIPO DE DISPOSITIVO
# ==========================================================

COMANDOS = {
    "mikrotik_routeros": {
        "nombre": "/system identity print",
        "recursos": "/system resource print",
        "interfaces": "/ip address print terse",
        "ruta_defecto": (
            "/ip route print terse "
            "where dst-address=0.0.0.0/0"
        )
    }
}


# ==========================================================
# INVENTARIO
# ==========================================================

def cargar_inventario():
    with open("inventario.yaml", "r", encoding="utf-8") as archivo:
        datos = yaml.safe_load(archivo)

    return datos["equipos"]


# ==========================================================
# CREDENCIALES
# ==========================================================

def obtener_password(nombre):
    variable = "LAB_PASS_" + nombre.upper().replace("-", "_")

    password = os.getenv(variable)

    if password is None:
        password = getpass.getpass(
            f"Contraseña para {nombre}: "
        )

    return password


# ==========================================================
# PARSERS
# ==========================================================

def texto_a_dict(salida):
    datos = {}

    for linea in salida.splitlines():
        if ":" in linea:
            clave, valor = linea.split(":", 1)
            datos[clave.strip()] = valor.strip()

    return datos


def parsear_terse(salida):
    registros = []

    for linea in salida.splitlines():

        linea = linea.strip()

        if not linea:
            continue

        registro = {}

        for parte in linea.split():
            if "=" in parte:
                clave, valor = parte.split("=", 1)
                registro[clave] = valor

        if registro:
            registros.append(registro)

    return registros


def obtener_gateway(rutas):
    if not rutas:
        return "-"

    return rutas[0].get("gateway", "-")


# ==========================================================
# CONEXIÓN Y RECOLECCIÓN
# ==========================================================

def conectar_equipo(equipo):
    nombre = equipo["nombre"]
    device_type = equipo["device_type"]

    dispositivo = {
        "device_type": device_type,
        "host": equipo["host"],
        "username": equipo["usuario"],
        "password": obtener_password(nombre),
        "session_log": f"logs/{nombre}.log",
        "fast_cli": False
    }

    resultado = {
        "equipo": nombre,
        "host": equipo["host"],
        "fecha_hora": datetime.now().astimezone().isoformat(
            timespec="seconds"
        ),
        "estado": "error",
        "datos": {
            "nombre": None,
            "uptime": None,
            "interfaces": [],
            "ruta_defecto": []
        }
    }

    try:
        print(
            f"\nConectando a {nombre} "
            f"({equipo['host']})..."
        )

        comandos = COMANDOS[device_type]

        with ConnectHandler(**dispositivo) as conexion:

            salida_nombre = conexion.send_command(
                comandos["nombre"]
            )

            salida_recursos = conexion.send_command(
                comandos["recursos"]
            )

            salida_interfaces = conexion.send_command(
                comandos["interfaces"]
            )

            salida_ruta = conexion.send_command(
                comandos["ruta_defecto"]
            )

        nombre_dict = texto_a_dict(salida_nombre)
        recursos_dict = texto_a_dict(salida_recursos)

        interfaces = parsear_terse(
            salida_interfaces
        )

        rutas = parsear_terse(
            salida_ruta
        )

        resultado["estado"] = "ok"

        resultado["datos"] = {
            "nombre": nombre_dict.get("name"),
            "uptime": recursos_dict.get("uptime"),
            "interfaces": interfaces,
            "ruta_defecto": rutas
        }

        print(f"[OK] Conexión exitosa con {nombre}")

    except NetmikoTimeoutException:

        resultado["estado"] = (
            "Error: tiempo de espera agotado"
        )

        print(
            f"[ERROR] Tiempo de espera agotado "
            f"en {nombre}"
        )

    except NetmikoAuthenticationException:

        resultado["estado"] = (
            "Error: credenciales incorrectas"
        )

        print(
            f"[ERROR] Credenciales incorrectas "
            f"en {nombre}"
        )

    except Exception as error:

        resultado["estado"] = f"Error: {error}"

        print(f"[ERROR] {nombre}: {error}")

    return resultado


# ==========================================================
# REPORTE JSON
# ==========================================================

def guardar_reporte(resultados):
    with open(
        "reporte_estado.json",
        "w",
        encoding="utf-8"
    ) as archivo:

        json.dump(
            resultados,
            archivo,
            indent=4,
            ensure_ascii=False
        )

    print(
        "\n[OK] Reporte guardado en "
        "reporte_estado.json"
    )


# ==========================================================
# TABLA RESUMEN
# ==========================================================

def mostrar_resumen(resultados):

    print("\n" + "=" * 90)
    print("RESUMEN DE EQUIPOS")
    print("=" * 90)

    print(
        f"{'Equipo':<15}"
        f"{'IP':<18}"
        f"{'Estado':<25}"
        f"{'Interfaces':<15}"
        f"{'Gateway':<17}"
    )

    print("-" * 90)

    for resultado in resultados:

        interfaces = resultado["datos"]["interfaces"]
        rutas = resultado["datos"]["ruta_defecto"]

        gateway = obtener_gateway(rutas)

        print(
            f"{resultado['equipo']:<15}"
            f"{resultado['host']:<18}"
            f"{resultado['estado']:<25}"
            f"{len(interfaces):<15}"
            f"{gateway:<17}"
        )

    print("=" * 90)


# ==========================================================
# MAIN
# ==========================================================

def main():

    equipos = cargar_inventario()

    resultados = []

    for equipo in equipos:
        resultado = conectar_equipo(equipo)
        resultados.append(resultado)

    guardar_reporte(resultados)

    mostrar_resumen(resultados)


if __name__ == "__main__":
    main()
