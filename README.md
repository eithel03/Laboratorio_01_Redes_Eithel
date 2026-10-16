# Laboratorio 1 - Redes Programables

## Descripción

Este laboratorio implementa un inventario, consulta de estado y configuración segura de dispositivos de red mediante Python, SSH y Netmiko.

El script principal lee los dispositivos desde un inventario YAML y permite administrar equipos de distintos fabricantes.

## Equipos utilizados

- **MikroTik RouterOS v7**
  - **IP:** `10.60.30.202`
  - **Driver Netmiko:** `mikrotik_routeros`
  - **Rol:** Lectura y escritura

- **Cisco IOS 3725**
  - **IP:** `10.60.30.203`
  - **Driver Netmiko:** `cisco_ios`
  - **Rol:** Solo lectura
  - Implementado como extra multivendor

## Requisitos

Se recomienda utilizar un entorno virtual de Python.

Crear el entorno:
```bash
python3 -m venv env
```

Activarlo:
```bash
source env/bin/activate
```

Instalar las dependencias:
```bash
pip install -r requirements.txt
```

## Inventario

Los equipos se encuentran definidos en `inventario.yaml`.

Las contraseñas no se almacenan en el inventario ni en el código. El script busca variables de entorno con el formato:
```bash
LAB_PASS_<NOMBRE>
```

Por ejemplo:
```bash
export LAB_PASS_MT_LAB="contraseña"
export LAB_PASS_CISCO_LAB="contraseña"
```

Si una variable no existe, la contraseña se solicita de forma segura mediante `getpass`.

## Ejecución

Para ejecutar el laboratorio:
```bash
python3 lab1_inventario.py
```

El programa realiza las siguientes acciones:
- Lee los equipos desde `inventario.yaml`.
- Se conecta mediante SSH utilizando Netmiko.
- Obtiene nombre, uptime, interfaces con IP y ruta por defecto.
- Convierte la información obtenida a estructuras de Python.
- Genera el archivo `reporte_estado.json`.
- Muestra un resumen en consola.
- Genera un `session_log` por equipo en la carpeta `logs/`.

## Configuración R6

Para el MikroTik con rol de escritura, el script asegura la existencia de:
- **Loopback:** `lo-ssh-10`
- **Dirección IP:** `10.253.0.10/32`

La configuración es **idempotente**: si los objetos ya existen, el programa no los duplica y muestra el mensaje `SIN CAMBIOS`.

Para eliminar únicamente los objetos creados por R6, ejecute:
```bash
python3 lab1_inventario.py --limpiar
```

## Extra Multivendor

Se agregó soporte para Cisco IOS utilizando el driver `cisco_ios`. El dispositivo Cisco se utiliza únicamente para consultas de lectura.

Debido a la versión antigua de IOS utilizada en el Cisco 3725, el entorno utiliza una versión compatible de Paramiko definida en `requirements.txt`.

## Extra: LAN, DHCP y rutas estáticas

Se agregó el script:

```text
configurar_lan_dhcp.py
```

Este script configura automáticamente las redes LAN utilizadas por las VPCS.

### Cisco
- Interfaz: `FastEthernet0/1`
- IP: `192.168.20.1/24`
- DHCP para `PC1`
- Ruta estática hacia `192.168.30.0/24` mediante `10.60.30.202`

### MikroTik
- Interfaz: `ether2`
- IP: `192.168.30.1/24`
- DHCP para `PC2`
- Ruta estática hacia `192.168.20.0/24` mediante `10.60.30.203`

### Ejecución
```bash
python3 configurar_lan_dhcp.py
```

Después, en las VPCS se puede solicitar dirección mediante DHCP:
```text
PC1> ip dhcp
PC2> ip dhcp
```

El script es idempotente, por lo que una segunda ejecución no duplica la configuración.

Para eliminar solamente la configuración creada por este script:
```bash
python3 configurar_lan_dhcp.py --limpiar
```
*Nota: Este comando no elimina la configuración principal utilizada por `lab1_inventario.py`.*

---

## Extra: Salida a Internet de GNS3

Se agregó el script:

```text
internet_gns3.sh
```

Este script configura Fedora como gateway para permitir que `PC1` y `PC2` tengan acceso a Internet.

El script realiza automáticamente:
- Detección de la interfaz de Fedora que tiene acceso a Internet.
- Creación de `tap0` si no existe.
- Configuración de `10.60.30.1/24` en `tap0`.
- Activación de IPv4 forwarding.
- Creación de rutas hacia `192.168.20.0/24` y `192.168.30.0/24`.
- Configuración de NAT mediante `nftables`.
- Prevención de reglas duplicadas.

### Ejecución
Dar permisos de ejecución:
```bash
chmod +x internet_gns3.sh
```

Ejecutar:
```bash
sudo ./internet_gns3.sh
```

El script detecta automáticamente la interfaz que Fedora utiliza para acceder a Internet, por lo que no depende de una red Wi-Fi específica.

Para eliminar el NAT, las rutas y el forwarding creados por este script:

```bash
sudo ./internet_gns3.sh --limpiar
```
*La opción `--limpiar` mantiene `tap0` y la dirección `10.60.30.1/24`, permitiendo conservar la conectividad entre Fedora, MikroTik y Cisco.*

---

## Pruebas de conectividad adicionales

Después de configurar DHCP, las rutas y la salida a Internet se comprobó:
- `PC1` $\rightarrow$ Cisco
- `PC2` $\rightarrow$ MikroTik
- `PC1` $\leftrightarrow$ `PC2`
- `PC1` $\rightarrow$ Internet
- `PC2` $\rightarrow$ Internet

También se verificó resolución DNS desde las VPCS mediante dominios como:
- `google.com`
- `youtube.com`

## Archivos Principales

- `README.md`
- `requirements.txt`
- `.gitignore`
- `inventario.yaml`
- `lab1_inventario.py`
- `reporte_estado.json`
- `logs/`
- `configurar_lan_dhcp.py`
- `internet_gns3.sh`

## Uso de Inteligencia Artificial

Para hacer el laboratorio utilicé inteligencia artificial como herramienta de apoyo para interpretar los requerimientos, explicar conceptos de Python, Netmiko, SSH, analizar errores durante las pruebas y ayudarme con la implementación del código.

Las configuraciones, conexiones y ejecuciones del laboratorio las realice y verifique yo con mi Fedora y en la topología de GNS3.
