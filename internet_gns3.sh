#!/usr/bin/env bash

set -u

TAP="tap0"
RED_GNS3="10.60.30.0/24"
IP_TAP="10.60.30.1/24"

RED_PC1="192.168.20.0/24"
GATEWAY_PC1="10.60.30.203"

RED_PC2="192.168.30.0/24"
GATEWAY_PC2="10.60.30.202"

TABLA_NFT="gns3_internet"


# ==========================================================
# VERIFICAR ROOT
# ==========================================================

if [[ "$EUID" -ne 0 ]]; then
    echo "[ERROR] Este script debe ejecutarse con sudo."
    echo
    echo "Ejemplo:"
    echo "sudo ./internet_gns3.sh"
    exit 1
fi


# ==========================================================
# FUNCION LIMPIAR
# ==========================================================

limpiar() {

    echo
    echo "=== LIMPIANDO CONFIGURACION DE INTERNET GNS3 ==="

    cambios=0

    # ------------------------------------------------------
    # ELIMINAR TABLA NFTABLES
    # ------------------------------------------------------

    if nft list table inet "$TABLA_NFT" >/dev/null 2>&1; then

        nft delete table inet "$TABLA_NFT"

        echo "[+] Reglas NAT y forwarding eliminadas"
        cambios=$((cambios + 1))

    else

        echo "[=] No existen reglas nftables del laboratorio"

    fi


    # ------------------------------------------------------
    # ELIMINAR RUTA HACIA PC1
    # ------------------------------------------------------

    if ip route show "$RED_PC1" | grep -q "$GATEWAY_PC1"; then

        ip route del "$RED_PC1" via "$GATEWAY_PC1"

        echo "[+] Ruta hacia PC1 eliminada"
        cambios=$((cambios + 1))

    else

        echo "[=] Ruta hacia PC1 no existe"

    fi


    # ------------------------------------------------------
    # ELIMINAR RUTA HACIA PC2
    # ------------------------------------------------------

    if ip route show "$RED_PC2" | grep -q "$GATEWAY_PC2"; then

        ip route del "$RED_PC2" via "$GATEWAY_PC2"

        echo "[+] Ruta hacia PC2 eliminada"
        cambios=$((cambios + 1))

    else

        echo "[=] Ruta hacia PC2 no existe"

    fi


    # ------------------------------------------------------
    # DESACTIVAR FORWARDING
    # ------------------------------------------------------

    if [[ "$(sysctl -n net.ipv4.ip_forward)" == "1" ]]; then

        sysctl -w net.ipv4.ip_forward=0 >/dev/null

        echo "[+] IPv4 forwarding desactivado"
        cambios=$((cambios + 1))

    else

        echo "[=] IPv4 forwarding ya estaba desactivado"

    fi


    # ------------------------------------------------------
    # RESULTADO
    # ------------------------------------------------------

    if [[ "$cambios" -eq 0 ]]; then

        echo
        echo "SIN CAMBIOS."

    else

        echo
        echo "[OK] Limpieza completada. Cambios: $cambios"

    fi

    echo
    echo "NOTA: tap0 y 10.60.30.1/24 se mantienen."
    echo "Esto permite que el laboratorio principal siga funcionando."
}


# ==========================================================
# ARGUMENTO --limpiar
# ==========================================================

if [[ "${1:-}" == "--limpiar" ]]; then

    limpiar
    exit 0

fi


# ==========================================================
# DETECTAR INTERFAZ CON INTERNET
# ==========================================================

echo
echo "=== CONFIGURANDO INTERNET PARA GNS3 ==="
echo

INTERFAZ_INTERNET=$(
    ip route get 1.1.1.1 2>/dev/null |
    awk '{
        for (i = 1; i <= NF; i++) {
            if ($i == "dev") {
                print $(i + 1)
                exit
            }
        }
    }'
)

if [[ -z "$INTERFAZ_INTERNET" ]]; then

    echo "[ERROR] No se pudo detectar una interfaz con Internet."
    exit 1

fi

echo "[OK] Interfaz con Internet detectada: $INTERFAZ_INTERNET"


# ==========================================================
# VERIFICAR TAP0
# ==========================================================

if ! ip link show "$TAP" >/dev/null 2>&1; then

    USUARIO_REAL="${SUDO_USER:-$USER}"

    ip tuntap add dev "$TAP" mode tap user "$USUARIO_REAL"

    echo "[+] Interfaz $TAP creada"

else

    echo "[=] Interfaz $TAP ya existe"

fi


# ==========================================================
# LEVANTAR TAP0
# ==========================================================

ip link set "$TAP" up

echo "[OK] $TAP está activa"


# ==========================================================
# CONFIGURAR IP DE TAP0
# ==========================================================

if ip addr show "$TAP" | grep -q "10.60.30.1/24"; then

    echo "[=] $TAP ya tiene 10.60.30.1/24"

else

    ip addr add "$IP_TAP" dev "$TAP"

    echo "[+] IP 10.60.30.1/24 agregada a $TAP"

fi


# ==========================================================
# ACTIVAR FORWARDING
# ==========================================================

if [[ "$(sysctl -n net.ipv4.ip_forward)" == "1" ]]; then

    echo "[=] IPv4 forwarding ya está activo"

else

    sysctl -w net.ipv4.ip_forward=1 >/dev/null

    echo "[+] IPv4 forwarding activado"

fi


# ==========================================================
# RUTA HACIA PC1
# ==========================================================

ip route replace "$RED_PC1" via "$GATEWAY_PC1"

echo "[OK] Ruta $RED_PC1 via $GATEWAY_PC1"


# ==========================================================
# RUTA HACIA PC2
# ==========================================================

ip route replace "$RED_PC2" via "$GATEWAY_PC2"

echo "[OK] Ruta $RED_PC2 via $GATEWAY_PC2"


# ==========================================================
# NFTABLES
# ==========================================================

# Eliminamos nuestra tabla si ya existe.
# Así nunca acumulamos reglas duplicadas.

if nft list table inet "$TABLA_NFT" >/dev/null 2>&1; then

    nft delete table inet "$TABLA_NFT"

fi


# ==========================================================
# CREAR TABLA
# ==========================================================

nft add table inet "$TABLA_NFT"


# ==========================================================
# FORWARDING
# ==========================================================

nft "add chain inet $TABLA_NFT forward {
    type filter hook forward priority 0;
    policy accept;
}"


# ==========================================================
# NAT POSTROUTING
# ==========================================================

nft "add chain inet $TABLA_NFT postrouting {
    type nat hook postrouting priority 100;
    policy accept;
}"


# ==========================================================
# NAT PC1
# ==========================================================

nft add rule inet "$TABLA_NFT" postrouting \
    oifname "$INTERFAZ_INTERNET" \
    ip saddr "$RED_PC1" \
    masquerade


# ==========================================================
# NAT PC2
# ==========================================================

nft add rule inet "$TABLA_NFT" postrouting \
    oifname "$INTERFAZ_INTERNET" \
    ip saddr "$RED_PC2" \
    masquerade


# ==========================================================
# RESULTADO
# ==========================================================

echo
echo "=============================================="
echo " CONFIGURACION COMPLETADA"
echo "=============================================="
echo
echo "Internet : $INTERFAZ_INTERNET"
echo "GNS3     : $TAP - $IP_TAP"
echo
echo "PC1 LAN  : $RED_PC1"
echo "Gateway  : $GATEWAY_PC1"
echo
echo "PC2 LAN  : $RED_PC2"
echo "Gateway  : $GATEWAY_PC2"
echo
echo "NAT      : ACTIVO"
echo "Forward  : ACTIVO"
echo
echo "=============================================="
