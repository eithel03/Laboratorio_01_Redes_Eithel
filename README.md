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

## Archivos Principales

- `README.md`
- `requirements.txt`
- `.gitignore`
- `inventario.yaml`
- `lab1_inventario.py`
- `reporte_estado.json`
- `logs/`

## Uso de Inteligencia Artificial

Para hacer el laboratorio utilicé inteligencia artificial como herramienta de apoyo para interpretar los requerimientos, explicar conceptos de Python, Netmiko, SSH, analizar errores durante las pruebas y ayudarme con la implementación del código.

Las configuraciones, conexiones y ejecuciones del laboratorio las realice y verifique yo con mi Fedora y en la topología de GNS3.
