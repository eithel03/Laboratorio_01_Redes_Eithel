#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
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
# CONFIGURACIÓN R6
# ==========================================================

NUMERO = 10
LOOPBACK = f"lo-ssh-{NUMERO}"
IP_LOOPBACK = f"10.253.0.{NUMERO}/32"
COMENTARIO = "Eithel-Lab1"


# ==========================================================
# INVENTARIO
# ==========================================================

def cargar_inventario():
    with open(
        "inventario.yaml",
        "r",
        encoding="utf-8"
    ) as archivo:

        datos = yaml.safe_load(archivo)

    return datos["equipos"]


# ==========================================================
# CREDENCIALES
# ==========================================================

def obtener_password(nombre):
    variable = (
        "LAB_PASS_"
        + nombre.upper().replace("-", "_")
    )

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

            datos[
                clave.strip()
            ] = valor.strip()

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

                clave, valor = parte.split(
                    "=",
                    1
                )

                registro[clave] = valor

        if registro:
            registros.append(registro)

    return registros


def obtener_gateway(rutas):
    if not rutas:
        return "-"

    return rutas[0].get(
        "gateway",
        "-"
    )


# ==========================================================
# R6 - CONFIGURACIÓN IDEMPOTENTE
# ==========================================================

def configurar_r6(conexion):

    cambios = 0

    print("\nVerificando configuración R6...")

    # ------------------------------------------------------
    # BRIDGE
    # ------------------------------------------------------

    salida_bridge = conexion.send_command(
        f"/interface bridge print terse "
        f"where name={LOOPBACK}"
    )

    if not salida_bridge:

        conexion.send_command(
            f'/interface bridge add '
            f'name={LOOPBACK} '
            f'comment="{COMENTARIO}"'
        )

        print(
            f"[+] Bridge {LOOPBACK} creado"
        )

        cambios += 1

    else:

        print(
            f"[=] Bridge {LOOPBACK} ya existe"
        )

    # ------------------------------------------------------
    # DIRECCIÓN IP
    # ------------------------------------------------------

    salida_ip = conexion.send_command(
        f"/ip address print terse "
        f"where interface={LOOPBACK}"
    )

    if IP_LOOPBACK not in salida_ip:

        conexion.send_command(
            f'/ip address add '
            f'address={IP_LOOPBACK} '
            f'interface={LOOPBACK} '
            f'comment="{COMENTARIO}"'
        )

        print(
            f"[+] IP {IP_LOOPBACK} agregada"
        )

        cambios += 1

    else:

        print(
            f"[=] IP {IP_LOOPBACK} ya existe"
        )

    # ------------------------------------------------------
    # VERIFICACIÓN
    # ------------------------------------------------------

    verificar_bridge = conexion.send_command(
        f"/interface bridge print terse "
        f"where name={LOOPBACK}"
    )

    verificar_ip = conexion.send_command(
        f"/ip address print terse "
        f"where interface={LOOPBACK}"
    )

    if (
        LOOPBACK in verificar_bridge
        and IP_LOOPBACK in verificar_ip
    ):

        print(
            "[OK] Configuración R6 verificada"
        )

    else:

        print(
            "[ERROR] No se pudo verificar "
            "la configuración R6"
        )

    # ------------------------------------------------------
    # RESULTADO
    # ------------------------------------------------------

    if cambios == 0:

        print(
            "SIN CAMBIOS: "
            "la configuración ya existía."
        )

    else:

        print(
            "Configuración completada. "
            f"Cambios realizados: {cambios}"
        )


# ==========================================================
# R6 - LIMPIAR
# ==========================================================

def limpiar_r6(conexion):

    print("\nLimpiando configuración R6...")

    cambios = 0

    # ------------------------------------------------------
    # ELIMINAR IP
    # ------------------------------------------------------

    salida_ip = conexion.send_command(
        f"/ip address print terse "
        f'where comment="{COMENTARIO}"'
    )

    if salida_ip:

        conexion.send_command(
            f"/ip address remove "
            f'[find where comment="{COMENTARIO}"]'
        )

        print(
            f"[-] IP {IP_LOOPBACK} eliminada"
        )

        cambios += 1

    else:

        print(
            "[=] No existe IP de R6 para eliminar"
        )

    # ------------------------------------------------------
    # ELIMINAR BRIDGE
    # ------------------------------------------------------

    salida_bridge = conexion.send_command(
        f"/interface bridge print terse "
        f"where name={LOOPBACK}"
    )

    if salida_bridge:

        conexion.send_command(
            f"/interface bridge remove "
            f'[find where name="{LOOPBACK}"]'
        )

        print(
            f"[-] Bridge {LOOPBACK} eliminado"
        )

        cambios += 1

    else:

        print(
            f"[=] Bridge {LOOPBACK} "
            "no existe"
        )

    if cambios == 0:

        print(
            "SIN CAMBIOS: "
            "no había objetos de R6."
        )

    else:

        print(
            "[OK] Limpieza de R6 completada."
        )


# ==========================================================
# CONEXIÓN Y RECOLECCIÓN
# ==========================================================

def conectar_equipo(
    equipo,
    limpiar=False
):

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
        "fecha_hora": (
            datetime.now()
            .astimezone()
            .isoformat(
                timespec="seconds"
            )
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

        comandos = COMANDOS[
            device_type
        ]

        with ConnectHandler(
            **dispositivo
        ) as conexion:

            # ==============================================
            # R6
            # Solo equipos con rol escritura
            # ==============================================

            if equipo["rol"] == "escritura":

                if limpiar:
                    limpiar_r6(
                        conexion
                    )

                else:
                    configurar_r6(
                        conexion
                    )

            # ==============================================
            # R4 - RECOLECTAR ESTADO
            # ==============================================

            salida_nombre = (
                conexion.send_command(
                    comandos["nombre"]
                )
            )

            salida_recursos = (
                conexion.send_command(
                    comandos["recursos"]
                )
            )

            salida_interfaces = (
                conexion.send_command(
                    comandos["interfaces"]
                )
            )

            salida_ruta = (
                conexion.send_command(
                    comandos["ruta_defecto"]
                )
            )

        nombre_dict = texto_a_dict(
            salida_nombre
        )

        recursos_dict = texto_a_dict(
            salida_recursos
        )

        interfaces = parsear_terse(
            salida_interfaces
        )

        rutas = parsear_terse(
            salida_ruta
        )

        resultado["estado"] = "ok"

        resultado["datos"] = {
            "nombre": nombre_dict.get(
                "name"
            ),
            "uptime": recursos_dict.get(
                "uptime"
            ),
            "interfaces": interfaces,
            "ruta_defecto": rutas
        }

        print(
            f"\n[OK] Conexión exitosa "
            f"con {nombre}"
        )

    except NetmikoTimeoutException:

        resultado["estado"] = (
            "Error: tiempo de espera agotado"
        )

        print(
            f"[ERROR] Tiempo de espera "
            f"agotado en {nombre}"
        )

    except NetmikoAuthenticationException:

        resultado["estado"] = (
            "Error: credenciales incorrectas"
        )

        print(
            f"[ERROR] Credenciales "
            f"incorrectas en {nombre}"
        )

    except Exception as error:

        resultado["estado"] = (
            f"Error: {error}"
        )

        print(
            f"[ERROR] {nombre}: {error}"
        )

    return resultado


# ==========================================================
# R5 - REPORTE JSON
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
# R5 - TABLA RESUMEN
# ==========================================================

def mostrar_resumen(resultados):

    print(
        "\n"
        + "=" * 100
    )

    print(
        "RESUMEN DE EQUIPOS"
    )

    print(
        "=" * 100
    )

    print(
        f"{'Equipo':<15}"
        f"{'IP':<18}"
        f"{'Estado':<35}"
        f"{'Interfaces':<15}"
        f"{'Gateway':<17}"
    )

    print(
        "-" * 100
    )

    for resultado in resultados:

        interfaces = (
            resultado[
                "datos"
            ][
                "interfaces"
            ]
        )

        rutas = (
            resultado[
                "datos"
            ][
                "ruta_defecto"
            ]
        )

        gateway = obtener_gateway(
            rutas
        )

        print(
            f"{resultado['equipo']:<15}"
            f"{resultado['host']:<18}"
            f"{resultado['estado']:<35}"
            f"{len(interfaces):<15}"
            f"{gateway:<17}"
        )

    print(
        "=" * 100
    )


# ==========================================================
# MAIN
# ==========================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Inventario, estado y "
            "configuración segura "
            "con Netmiko"
        )
    )

    parser.add_argument(
        "--limpiar",
        action="store_true",
        help=(
            "Eliminar únicamente "
            "la configuración creada "
            "por R6"
        )
    )

    args = parser.parse_args()

    equipos = cargar_inventario()

    resultados = []

    for equipo in equipos:

        resultado = conectar_equipo(
            equipo,
            limpiar=args.limpiar
        )

        resultados.append(
            resultado
        )

    guardar_reporte(
        resultados
    )

    mostrar_resumen(
        resultados
    )


if __name__ == "__main__":
    main()
