#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import getpass

from netmiko import ConnectHandler
from netmiko.exceptions import (
    NetmikoAuthenticationException,
    NetmikoTimeoutException,
)


# ==========================================================
# DATOS DE LOS EQUIPOS
# ==========================================================

MIKROTIK = {
    "device_type": "mikrotik_routeros",
    "host": "10.60.30.202",
    "username": "lab-ssh",
}

CISCO = {
    "device_type": "cisco_ios",
    "host": "10.60.30.203",
    "username": "lab-ssh",
}


# ==========================================================
# MIKROTIK - CONFIGURAR
# ==========================================================

def configurar_mikrotik(password):

    dispositivo = MIKROTIK.copy()
    dispositivo["password"] = password
    dispositivo["fast_cli"] = False

    print("\n=== CONFIGURANDO MIKROTIK ===")

    try:
        with ConnectHandler(**dispositivo) as conexion:

            cambios = 0

            # --------------------------------------------------
            # IP LAN EN ETHER2
            # --------------------------------------------------

            salida = conexion.send_command(
                "/ip address print terse"
            )

            if (
                "192.168.30.1/24" not in salida
                or "interface=ether2" not in salida
            ):

                conexion.send_command(
                    '/ip address add '
                    'address=192.168.30.1/24 '
                    'interface=ether2 '
                    'comment="LAB1-PC2"'
                )

                print("[+] IP 192.168.30.1/24 agregada a ether2")
                cambios += 1

            else:

                print("[=] IP de ether2 ya existe")

            # --------------------------------------------------
            # POOL DHCP
            # --------------------------------------------------

            salida = conexion.send_command(
                "/ip pool print terse"
            )

            if "name=pool-pc2" not in salida:

                conexion.send_command(
                    '/ip pool add '
                    'name=pool-pc2 '
                    'ranges=192.168.30.10-192.168.30.100'
                )

                print("[+] Pool DHCP de PC2 creado")
                cambios += 1

            else:

                print("[=] Pool DHCP de PC2 ya existe")

            # --------------------------------------------------
            # SERVIDOR DHCP
            # --------------------------------------------------

            salida = conexion.send_command(
                "/ip dhcp-server print terse"
            )

            if "name=dhcp-pc2" not in salida:

                conexion.send_command(
                    '/ip dhcp-server add '
                    'name=dhcp-pc2 '
                    'interface=ether2 '
                    'address-pool=pool-pc2 '
                    'disabled=no'
                )

                print("[+] Servidor DHCP de PC2 creado")
                cambios += 1

            else:

                print("[=] Servidor DHCP de PC2 ya existe")

            # --------------------------------------------------
            # RED DHCP
            # --------------------------------------------------

            salida = conexion.send_command(
                "/ip dhcp-server network print terse"
            )

            if "192.168.30.0/24" not in salida:

                conexion.send_command(
                    '/ip dhcp-server network add '
                    'address=192.168.30.0/24 '
                    'gateway=192.168.30.1 '
                    'dns-server=1.1.1.1,8.8.8.8 '
                    'comment="LAB1-PC2"'
                )

                print("[+] Red DHCP de PC2 creada")
                cambios += 1

            else:

                print("[=] Red DHCP de PC2 ya existe")

            # --------------------------------------------------
            # RUTA ESTATICA HACIA PC1
            # --------------------------------------------------

            salida = conexion.send_command(
                "/ip route print terse"
            )

            if (
                "dst-address=192.168.20.0/24" not in salida
                or "gateway=10.60.30.203" not in salida
            ):

                conexion.send_command(
                    '/ip route add '
                    'dst-address=192.168.20.0/24 '
                    'gateway=10.60.30.203 '
                    'comment="LAB1-RUTA-PC1"'
                )

                print(
                    "[+] Ruta a 192.168.20.0/24 "
                    "via 10.60.30.203 creada"
                )

                cambios += 1

            else:

                print(
                    "[=] Ruta hacia 192.168.20.0/24 ya existe"
                )

            # --------------------------------------------------
            # RESULTADO
            # --------------------------------------------------

            if cambios == 0:

                print("SIN CAMBIOS en MikroTik.")

            else:

                print(
                    f"[OK] MikroTik configurado. "
                    f"Cambios: {cambios}"
                )

    except NetmikoAuthenticationException:

        print("[ERROR] Credenciales incorrectas en MikroTik")

    except NetmikoTimeoutException:

        print("[ERROR] No se pudo conectar al MikroTik")

    except Exception as error:

        print(f"[ERROR] MikroTik: {error}")


# ==========================================================
# MIKROTIK - LIMPIAR
# ==========================================================

def limpiar_mikrotik(password):

    dispositivo = MIKROTIK.copy()
    dispositivo["password"] = password
    dispositivo["fast_cli"] = False

    print("\n=== LIMPIANDO MIKROTIK ===")

    try:
        with ConnectHandler(**dispositivo) as conexion:

            cambios = 0

            # --------------------------------------------------
            # RUTA ESTATICA HACIA PC1
            # --------------------------------------------------

            salida = conexion.send_command(
                "/ip route print terse"
            )

            if (
                "dst-address=192.168.20.0/24" in salida
                and "gateway=10.60.30.203" in salida
            ):

                conexion.send_command(
                    '/ip route remove '
                    '[find dst-address="192.168.20.0/24" '
                    'gateway="10.60.30.203"]'
                )

                print("[+] Ruta hacia PC1 eliminada")
                cambios += 1

            else:

                print("[=] Ruta hacia PC1 no existe")

            # --------------------------------------------------
            # SERVIDOR DHCP
            # --------------------------------------------------

            salida = conexion.send_command(
                "/ip dhcp-server print terse"
            )

            if "name=dhcp-pc2" in salida:

                conexion.send_command(
                    '/ip dhcp-server remove '
                    '[find name="dhcp-pc2"]'
                )

                print("[+] Servidor DHCP de PC2 eliminado")
                cambios += 1

            else:

                print("[=] Servidor DHCP de PC2 no existe")

            # --------------------------------------------------
            # RED DHCP
            # --------------------------------------------------

            salida = conexion.send_command(
                "/ip dhcp-server network print terse"
            )

            if "192.168.30.0/24" in salida:

                conexion.send_command(
                    '/ip dhcp-server network remove '
                    '[find address="192.168.30.0/24"]'
                )

                print("[+] Red DHCP de PC2 eliminada")
                cambios += 1

            else:

                print("[=] Red DHCP de PC2 no existe")

            # --------------------------------------------------
            # POOL DHCP
            # --------------------------------------------------

            salida = conexion.send_command(
                "/ip pool print terse"
            )

            if "name=pool-pc2" in salida:

                conexion.send_command(
                    '/ip pool remove '
                    '[find name="pool-pc2"]'
                )

                print("[+] Pool DHCP de PC2 eliminado")
                cambios += 1

            else:

                print("[=] Pool DHCP de PC2 no existe")

            # --------------------------------------------------
            # IP EN ETHER2
            # --------------------------------------------------

            salida = conexion.send_command(
                "/ip address print terse"
            )

            if (
                "192.168.30.1/24" in salida
                and "interface=ether2" in salida
            ):

                conexion.send_command(
                    '/ip address remove '
                    '[find address="192.168.30.1/24" '
                    'interface="ether2"]'
                )

                print(
                    "[+] IP 192.168.30.1/24 "
                    "eliminada de ether2"
                )

                cambios += 1

            else:

                print("[=] IP creada por este script no existe")

            # --------------------------------------------------
            # RESULTADO
            # --------------------------------------------------

            if cambios == 0:

                print("SIN CAMBIOS en MikroTik.")

            else:

                print(
                    f"[OK] Limpieza MikroTik completada. "
                    f"Cambios: {cambios}"
                )

    except NetmikoAuthenticationException:

        print("[ERROR] Credenciales incorrectas en MikroTik")

    except NetmikoTimeoutException:

        print("[ERROR] No se pudo conectar al MikroTik")

    except Exception as error:

        print(f"[ERROR] MikroTik: {error}")


# ==========================================================
# CISCO - CONFIGURAR
# ==========================================================

def configurar_cisco(password):

    dispositivo = CISCO.copy()
    dispositivo["password"] = password
    dispositivo["fast_cli"] = False

    print("\n=== CONFIGURANDO CISCO ===")

    try:
        with ConnectHandler(**dispositivo) as conexion:

            cambios = 0

            # --------------------------------------------------
            # INTERFAZ FASTETHERNET0/1
            # --------------------------------------------------

            salida = conexion.send_command(
                "show running-config interface FastEthernet0/1"
            )

            if "192.168.20.1 255.255.255.0" not in salida:

                conexion.send_config_set([
                    "interface FastEthernet0/1",
                    "ip address 192.168.20.1 255.255.255.0",
                    "no shutdown",
                ])

                print(
                    "[+] Fa0/1 configurada "
                    "con 192.168.20.1/24"
                )

                cambios += 1

            else:

                print("[=] Fa0/1 ya tiene la IP correcta")

            # --------------------------------------------------
            # EXCLUSIONES DHCP
            # --------------------------------------------------

            salida = conexion.send_command(
                "show running-config | "
                "include ip dhcp excluded-address"
            )

            exclusion = (
                "ip dhcp excluded-address "
                "192.168.20.1 192.168.20.9"
            )

            if exclusion not in salida:

                conexion.send_config_set([
                    exclusion
                ])

                print("[+] Direcciones reservadas en Cisco")
                cambios += 1

            else:

                print("[=] Exclusiones DHCP ya existen")

            # --------------------------------------------------
            # POOL DHCP
            # --------------------------------------------------

            salida = conexion.send_command(
                "show running-config | section ip dhcp pool PC1"
            )

            if "ip dhcp pool PC1" not in salida:

                conexion.send_config_set([
                    "ip dhcp pool PC1",
                    "network 192.168.20.0 255.255.255.0",
                    "default-router 192.168.20.1",
                    "dns-server 1.1.1.1 8.8.8.8",
                ])

                print("[+] Pool DHCP PC1 creado")
                cambios += 1

            else:

                print("[=] Pool DHCP PC1 ya existe")

            # --------------------------------------------------
            # RUTA ESTATICA HACIA PC2
            # --------------------------------------------------

            salida = conexion.send_command(
                "show running-config | include ^ip route"
            )

            ruta = (
                "ip route 192.168.30.0 "
                "255.255.255.0 "
                "10.60.30.202"
            )

            if ruta not in salida:

                conexion.send_config_set([
                    ruta
                ])

                print(
                    "[+] Ruta a 192.168.30.0/24 "
                    "via 10.60.30.202 creada"
                )

                cambios += 1

            else:

                print(
                    "[=] Ruta hacia 192.168.30.0/24 ya existe"
                )

            # --------------------------------------------------
            # GUARDAR CONFIGURACION
            # --------------------------------------------------

            conexion.save_config()

            # --------------------------------------------------
            # RESULTADO
            # --------------------------------------------------

            if cambios == 0:

                print("SIN CAMBIOS en Cisco.")

            else:

                print(
                    f"[OK] Cisco configurado. "
                    f"Cambios: {cambios}"
                )

    except NetmikoAuthenticationException:

        print("[ERROR] Credenciales incorrectas en Cisco")

    except NetmikoTimeoutException:

        print("[ERROR] No se pudo conectar al Cisco")

    except Exception as error:

        print(f"[ERROR] Cisco: {error}")


# ==========================================================
# CISCO - LIMPIAR
# ==========================================================

def limpiar_cisco(password):

    dispositivo = CISCO.copy()
    dispositivo["password"] = password
    dispositivo["fast_cli"] = False

    print("\n=== LIMPIANDO CISCO ===")

    try:
        with ConnectHandler(**dispositivo) as conexion:

            cambios = 0

            # --------------------------------------------------
            # RUTA ESTATICA HACIA PC2
            # --------------------------------------------------

            salida = conexion.send_command(
                "show running-config | include ^ip route"
            )

            ruta = (
                "ip route 192.168.30.0 "
                "255.255.255.0 "
                "10.60.30.202"
            )

            if ruta in salida:

                conexion.send_config_set([
                    "no " + ruta
                ])

                print("[+] Ruta hacia PC2 eliminada")
                cambios += 1

            else:

                print("[=] Ruta hacia PC2 no existe")

            # --------------------------------------------------
            # POOL DHCP
            # --------------------------------------------------

            salida = conexion.send_command(
                "show running-config | section ip dhcp pool PC1"
            )

            if "ip dhcp pool PC1" in salida:

                conexion.send_config_set([
                    "no ip dhcp pool PC1"
                ])

                print("[+] Pool DHCP PC1 eliminado")
                cambios += 1

            else:

                print("[=] Pool DHCP PC1 no existe")

            # --------------------------------------------------
            # EXCLUSIONES DHCP
            # --------------------------------------------------

            salida = conexion.send_command(
                "show running-config | "
                "include ip dhcp excluded-address"
            )

            exclusion = (
                "ip dhcp excluded-address "
                "192.168.20.1 192.168.20.9"
            )

            if exclusion in salida:

                conexion.send_config_set([
                    "no " + exclusion
                ])

                print("[+] Exclusiones DHCP eliminadas")
                cambios += 1

            else:

                print("[=] Exclusiones DHCP no existen")

            # --------------------------------------------------
            # IP DE FASTETHERNET0/1
            # --------------------------------------------------

            salida = conexion.send_command(
                "show running-config interface FastEthernet0/1"
            )

            if "192.168.20.1 255.255.255.0" in salida:

                conexion.send_config_set([
                    "interface FastEthernet0/1",
                    "no ip address 192.168.20.1 255.255.255.0",
                ])

                print(
                    "[+] IP 192.168.20.1/24 "
                    "eliminada de Fa0/1"
                )

                cambios += 1

            else:

                print("[=] IP creada por este script no existe")

            # --------------------------------------------------
            # GUARDAR CONFIGURACION
            # --------------------------------------------------

            conexion.save_config()

            # --------------------------------------------------
            # RESULTADO
            # --------------------------------------------------

            if cambios == 0:

                print("SIN CAMBIOS en Cisco.")

            else:

                print(
                    f"[OK] Limpieza Cisco completada. "
                    f"Cambios: {cambios}"
                )

    except NetmikoAuthenticationException:

        print("[ERROR] Credenciales incorrectas en Cisco")

    except NetmikoTimeoutException:

        print("[ERROR] No se pudo conectar al Cisco")

    except Exception as error:

        print(f"[ERROR] Cisco: {error}")


# ==========================================================
# MAIN
# ==========================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Configurar LAN, DHCP y rutas estaticas "
            "en MikroTik y Cisco"
        )
    )

    parser.add_argument(
        "--limpiar",
        action="store_true",
        help=(
            "Eliminar solo la configuracion "
            "gestionada por este script"
        ),
    )

    args = parser.parse_args()

    password_mt = getpass.getpass(
        "Contraseña MikroTik: "
    )

    password_cisco = getpass.getpass(
        "Contraseña Cisco: "
    )

    if args.limpiar:

        limpiar_mikrotik(password_mt)
        limpiar_cisco(password_cisco)

    else:

        configurar_mikrotik(password_mt)
        configurar_cisco(password_cisco)


if __name__ == "__main__":
    main()
