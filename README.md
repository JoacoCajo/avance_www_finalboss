# Grupo Miku-laso

## Integrantes

- Cristóbal Espinoza - 202273565-1
- Sebastián Canales - 202273640-2
- Diego Sierra - 202273531-7
- Adán Contreras - 202273519-8
- Joaquín Viveros - 202273586-4
- **Profesor**: Ernesto Vivanco

## Videos

- [Video Prototipo Figma](https://drive.google.com/file/d/1SyKwpuH8fTFR4A4p5z9H_1R0DA4h9Un-/view?usp=sharing)

## Navegación por la Página
Para esta primera presentación, el frontend de la página se está trabajando con el programa *Figma*.
Para visualizar la página, se deberán seguir estos pasos:
1. Abrir el [link](https://www.figma.com/design/QKW7akjVrPoWDboq9zrnYR/Biblioteca-de-libros-libreros?node-id=23-3&t=hBhKfm0hYHWpOSSy-1) al Figma de la página.
2. Dentro, en el panel de la izquierda, se encontrarán las tres páginas disponibles que hemos trabajado:
    - Dashboard y revisiones
    - Consulta y solicitud
    - Log-in y registro
3. Clickear cualquiera de estas páginas.
4. Dentro se podrán ver los *frames* y *componentes*.
5. Para ver la presentación de la página, pulsar el botón con forma de *"play"*, ubicado arriba a la derecha.
6. Probar los distintos botones, o utilizando las flechas de desplazamiento que apareceran en la parte central inferior de la página.

## COMO EJECUTAR EL PROYECTO:
1) Descargar el proyecto a través de git clone
2) CONFIGURAR LA BASE DE DATOS:
    2.1) ejecutan el Docker: docker-compose up -d postgres
    2.2) ejecutar: docker exec -i biblioteca_postgres \
        psql -U biblioteca_user -d biblioteca_db < schema.sql

    2.3) Verificar que está todo correcto:

        docker exec -it biblioteca_postgres bash

        luego, estando en la consola bash:

        psql -U biblioteca_user -d biblioteca_db

        en este punto ya están en la consola de postgres:

        SELECT * FROM bibliotecas;
        SELECT * FROM usuarios;

3) Creamos un entorno virtual, entramos a él y cargamos el archivo requirements.txt para tener todas librerias y módulos disponibles.
4) Ejecutamos, en dos consolas distintas, frontend y backend, de la siguiente forma:
    4.1) Para frontend: npm run dev (importante hacer 'npm install' antes)
    4.2) Para backend: python3 -m uvicorn app.main:app --reload --port 8009
5) Ingresamos a localhost:8080.
6) La página se muestra correctamente.


