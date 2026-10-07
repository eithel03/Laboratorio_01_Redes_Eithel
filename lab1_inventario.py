#!/usr/bin/env python3

import os
import getpass
import yaml

from netmiko import ConnectHandler
from netmiko.exceptions import (
    NetmikoTimeoutException,
    NetmikoAuthenticationException
)


def cargar_inventario():
    with open("inventario.yaml", "r", encoding="utf-8") as archivo:
        datos = yaml.safe_load(archivo)

    return datos["equipos"]


def obtener_password(nombre):
    variable = "LAB_PASS_" + nombre.upper().replace("-", "_")

    password = os.getenv(variable)

    if password is None:
        password = getpass.getpass(
            f"Contraseña para {nombre}: "
        )

    return password


def conectar_equipo(equipo):
    nombre = equipo["nombre"]

    dispositivo = {
        "device_type": equipo["device_type"],
        "host": equipo["host"],
        "username": equipo["usuario"],
        "password": obtener_password(nombre),
        "session_log": f"logs/{nombre}.log"
    }

    try:
        print(f"\nConectando a {nombre} ({equipo['host']})...")

        with ConnectHandler(**dispositivo) as conexion:

            salida = conexion.send_command(
                "/system identity print"
            )

            print(f"[OK] Conexión exitosa con {nombre}")
            print(salida)

    except NetmikoTimeoutException:
        print(f"[ERROR] Tiempo de espera agotado en {nombre}")

    except NetmikoAuthenticationException:
        print(f"[ERROR] Credenciales incorrectas en {nombre}")

    except Exception as error:
        print(f"[ERROR] {nombre}: {error}")


def main():

    equipos = cargar_inventario()

    for equipo in equipos:
        conectar_equipo(equipo)


if __name__ == "__main__":
    main()
