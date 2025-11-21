# Sistema de Gestión para Gimnasio (GymLite)

![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-Framework-red)
![SQLite](https://img.shields.io/badge/Database-SQLite-green)
![Status](https://img.shields.io/badge/Status-Finalizado-brightgreen)

Este proyecto implementa un sistema centralizado de gestión de bases de datos para un gimnasio. El software soluciona problemas de redundancia, fragmentación de datos y procesos manuales, ofreciendo una interfaz web intuitiva para la administración de socios, pagos, clases y reservas.

Desarrollado como parte del curso **Base de Datos (2025-II)** de la Universidad Finis Terrae.


## 📋 Tabla de Contenidos
1. [Características Principales](#-características-principales)
2. [Arquitectura y Tecnologías](#-arquitectura-y-tecnologías)
3. [Estructura del Proyecto](#-estructura-del-proyecto)
4. [Instalación y Despliegue](#-instalación-y-despliegue)
5. [Uso del Sistema](#-uso-del-sistema)
6. [Autores](#-autores)


## 🚀 Características Principales

El sistema no solo cumple con los requisitos funcionales básicos (CRUD), sino que integra lógica de negocio avanzada directamente en la base de datos:

* **Gestión Integral:** Administración de Socios, Instructores, Clases, Pagos y Reservas.
* **Integridad Referencial Avanzada (Soft Delete):** Implementación de "Borrado Lógico" para asegurar la persistencia histórica de los datos (especialmente financieros) y permitir auditorías.
* **Lógica de Negocio en BD (Triggers):**
    * Control automático de aforo en clases.
    * Validación de vigencias de membresía.
    * Prevención de condiciones de carrera (*Race Conditions*).
* **Dashboard en Tiempo Real:** Visualización de métricas clave (ingresos mensuales, clases más populares, etc.).
* **Smart Seeding:** Mecanismos de carga dinámica de datos para facilitar el despliegue inicial y pruebas.


## 🛠 Arquitectura y Tecnologías

* **Lenguaje:** Python 3.11+
* **Framework Web:** Streamlit
* **Base de Datos:** SQLite (Implementación relacional compatible con SQL estándar)
* **Diseño:** Modelo Entidad-Relación normalizado.


## 📂 Estructura del Proyecto

```text
.
├── BDD-Sistema-de-gestión-para-gimnasio.drawio  # Diagrama de la Base de Datos
├── docs/                                        # Documentación e Informe LaTeX
│   └── InformeLatex/
├── interfaz/                                    # Código Fuente de la Aplicación
│   ├── app.py                                   # Punto de entrada (Main)
│   ├── auth_local.py                            # Módulo de autenticación
│   ├── database.py                              # Conexión y queries a la BD
│   ├── navbar.py                                # Componente de navegación
│   ├── requirements.txt                         # Dependencias de Python
│   ├── views/                                   # Vistas de Streamlit (Páginas)
│   │   ├── clases.py
│   │   ├── dashboard.py
│   │   ├── pagos.py
│   │   └── socios.py
│   └── GymLite.db                               # Archivo de Base de Datos principal
├── schema.sql                                   # Script de creación de tablas/triggers
├── seed.sql                                     # Script de datos de prueba
└── reset.sql                                    # Script para reiniciar la BDD
```


## 💻 Instalación y Despliegue

Sigue estos pasos para ejecutar el proyecto en tu entorno local:

### 1\. Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd <nombre-del-carpeta>
```

### 2\. Instalar dependencias

Navega a la carpeta de la interfaz e instala los requisitos:

```bash
cd interfaz
pip install -r requirements.txt
```

### 3\. Inicializar la Base de Datos

El sistema utiliza SQLite. Si necesitas reiniciar la base de datos con los datos de prueba (Seed), puedes ejecutar los scripts SQL proporcionados (`schema.sql` y `seed.sql`) o utilizar la funcionalidad de reset integrada si está disponible en la app.

### 4\. Ejecutar la Aplicación

Desde la carpeta `interfaz/`:

```bash
streamlit run app.py
```

El sistema debería abrirse automáticamente en tu navegador en `http://localhost:8501`.


## 📖 Uso del Sistema

1.  **Login:** Utiliza las credenciales por defecto de administrador(usuario: `admin`, contrasena: `Admin1234!`) o registra nueva cuenta.
2.  **Dashboard:** Vista general de KPIs del gimnasio.
3.  **Socios:** Registrar nuevos miembros, editar información y realizar "Soft Delete" (cambiar estado a inactivo).
4.  **Clases:** Programar clases y gestionar el aforo. Los *Triggers* impedirán reservas si se supera la capacidad.
5.  **Pagos:** Registro de transacciones financieras.


## 👥 Autores

**Universidad Finis Terrae - Facultad de Ingeniería**

  * **Alan Oliva** - [aolivah@uft.edu](mailto:aolivah@uft.edu)
  * **Tomas Tamayo** - [ttmayoa@uft.edu](mailto:ttmayoa@uft.edu)
  * **Esteban Marques** - [emarques\_@uft.edu](mailto:emarques_@uft.edu)
