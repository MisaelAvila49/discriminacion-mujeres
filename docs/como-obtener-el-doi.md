# Cómo obtener el DOI de este tablero

Un DOI (Digital Object Identifier) es un identificador permanente. Sirve para
que alguien pueda citar el tablero en un artículo y que ese enlace siga
funcionando aunque el repositorio cambie de nombre, de dueño o de servidor.
Sin él, la cita queda apuntando a una URL de GitHub que puede romperse.

La ruta que se describe aquí es **Zenodo**, que es gratuito, lo opera el CERN
y es el camino habitual para software y datos académicos. Emite DOIs de
DataCite sin costo y sin necesidad de que la universidad tenga convenio.

## Antes de empezar

Se necesitan tres cosas, y conviene resolverlas en este orden porque la
tercera no se puede cambiar después de publicar:

1. **El repositorio tiene que ser público.** Zenodo no puede leer repos
   privados. Hoy `MisaelAvila49/discriminacion-mujeres` ya lo es.

2. **Tiene que haber una licencia.** Zenodo la pide y, más de fondo, sin
   licencia nadie sabe si puede reutilizar el tablero. La casilla de
   Licencia en la portada dice "por definir", así que esto sigue pendiente.
   Para un producto de datos públicos del INEGI, las dos opciones razonables
   son CC BY 4.0 (atribución, la más común en datos abiertos) o MIT (si se
   quiere tratar como software). Es una decisión del equipo, no técnica.

3. **Definir quién es el autor de correspondencia**, porque Zenodo lo usa
   para los avisos. En la portada ya figura Wilfrido Gómez Arias.

## Procedimiento

1. Entrar a <https://zenodo.org> y elegir **Log in with GitHub**. Conviene
   usar la cuenta institucional o la que administre el repositorio.

2. Autorizar la aplicación de Zenodo cuando GitHub lo pida. Los permisos que
   solicita son de lectura de repos y de webhooks: es lo que necesita para
   enterarse de los *releases*.

3. Ir a <https://zenodo.org/account/settings/github/> y **activar el
   interruptor** del repositorio `discriminacion-mujeres`. Si el repositorio
   pertenece a una organización, un propietario de la organización tiene que
   aprobar el acceso de Zenodo antes de que aparezca en esa lista.

4. **Crear un release en GitHub.** Este es el paso que dispara todo: Zenodo
   archiva el repositorio y emite un DOI nuevo *cada vez* que se publica un
   release. Un tag sin release no basta.

   ```bash
   git tag -a v1.0.0 -m "Primera versión pública del tablero"
   git push origin v1.0.0
   ```

   Y luego, en la pestaña Releases de GitHub, publicar el release sobre ese
   tag con una descripción de qué incluye.

5. **Esperar unos minutos** y volver a Zenodo. El depósito aparece con su
   DOI. Zenodo entrega en realidad **dos**:

   - un DOI *de concepto*, que siempre apunta a la versión más reciente;
   - un DOI *de versión*, que apunta a esa versión concreta y nunca cambia.

   Para la portada conviene el DOI de concepto, porque el tablero se sigue
   actualizando. En un artículo que cita una cifra específica conviene el de
   versión, para que el número citado siga siendo verificable.

6. **Completar los metadatos en Zenodo.** El formulario se llena solo a
   partir del `CITATION.cff` del repositorio, pero conviene revisar que los
   tres autores estén en orden y con su ORCID, y que el tipo de depósito sea
   *Dataset* y no *Software*.

## Después de tener el DOI

Hay que escribirlo en dos lugares, o quedará colgando en Zenodo sin que nadie
lo encuentre:

1. **`CITATION.cff`**, descomentando el bloque que ya está preparado al final
   del archivo:

   ```yaml
   identifiers:
     - type: doi
       value: 10.5281/zenodo.XXXXXXX
       description: "DOI de todas las versiones"
   ```

2. **`src/index.md`**, sustituyendo el marcador de la portada:

   ```html
   <div class="book-meta-field">
     <span class="book-meta-label">DOI</span>
     <span class="book-meta-value"><a href="https://doi.org/10.5281/zenodo.XXXXXXX">10.5281/zenodo.XXXXXXX</a></span>
   </div>
   ```

   y agregándolo a los cuatro formatos del bloque "Cómo citar este tablero",
   porque una cita sin DOI pierde justamente lo que lo hace permanente.

## Qué hace `CITATION.cff` por sí solo

Aunque el DOI tarde en llegar, el archivo ya sirve: GitHub detecta
`CITATION.cff` en la rama principal y muestra un botón **Cite this
repository** en la portada del repo, que genera la cita en APA y BibTeX sin
que nadie tenga que copiarla a mano. También es de donde Zenodo toma los
metadatos, así que mantenerlo al día ahorra el trabajo del paso 6.
