# Projecte final del nivell C1

## Requisits

Per executar el codi en macOS, cal instal·lar [Docker Desktop](https://www.docker.com/products/docker-desktop/).

## Inici dels contenidors

Una vegada iniciat Docker Desktop, inicieu els contenidors amb la següent ordre:

```shell
docker-compose up
```

## Inicialització de la base de dades

L'avantatge d'utilitzar un entorn virtual és que permet aïllar les
dependències del projecte de les del sistema operatiu, evitant conflictes
entre diferents projectes i versions de biblioteques.

Per utilitzar el codi, primer cal preparar l'entorn virtual i instal·lar les
dependències. Es pot utilitzar venv o conda per crear l'entorn virtual.

Un cop creat i activat l'entorn virtual, ja es pot executar el codi per a
inicialitzar la base de dades.

> [!NOTE]
> Podeu utilitzar l'extensió de Visual Studio Code
> [Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python)
> per gestionar entorns virtuals i executar codi Python dins de l'editor.
> Per crear un entorn virtual amb venv o conda, accediu a la paleta d'ordres
> (`Ctrl+Shift+P` o `Cmd+Shift+P` a macOS) i escriviu "Python: Create Environment".

> [!IMPORTANT]
> Si voleu canviar l'intèrpret de Python utilitzat per Visual Studio Code,
> podeu fer-ho des de la paleta d'ordres (`Ctrl+Shift+P` o `Cmd+Shift+P` a macOS)
> escrivint "Python: Select Interpreter" i seleccionant l'intèrpret de l'entorn
> virtual que heu creat. Cal tenir en compte que l'intèrpret se seleccionarà
> automàticament amb l'entorn virtual quant aquest s'hagi creat amb l'extensió
> comentada en la nota anterior.

### Creació de l'entorn virtual amb venv

Per crear un entorn virtual amb venv, executeu la següent ordre al directori
arrel del projecte:

```sh
python3 -m venv .venv
```

Per tal d'assegurar que l'entorn virtual s'ha creat correctament, podeu
comprovar que el directori `.venv/` s'ha creat al directori arrel del projecte.

> [!TIP]
> En macos, python ja inclou venv per defecte. En altres sistemes operatius,
> pot ser necessari instal·lar el paquet `python3-venv`. Per exemple, en sistemes
> basats en Debian/Ubuntu, podeu instal·lar-lo amb l'ordre següent:

```sh
sudo apt-get install python3-venv
```

### Activació i desactivació de l'entorn virtual amb venv

Per activar l'entorn virtual, executeu la següent ordre:

```sh
source .venv/bin/activate
```

Per a desactivar l'entorn virtual, executeu la següent ordre:

```sh
deactivate
```

### Instal·lació i actualització de dependències amb venv

Per a instal·lar les biblioteques de Python es pot utilitzar el fitxer
`requirements.txt` amb l'ordre:

```sh
python3 -m pip install -r requirements.txt
```

Si no voleu utilitzar el fitxer `requirements.txt`, podeu instal·lar les
biblioteques necessàries amb la següent ordre després d'activar l'entorn virtual:

```sh
python3 -m pip install requests --upgrade pip
```

Un cop instal·lades les dependències, es poden actualitzar amb l'ordre:

```sh
python3 -m pip install --upgrade requests
```

> [!IMPORTANT]
> Assegureu-vos d'estar dins de l'entorn virtual abans d'instal·lar o
> actualitzar les dependències.

### Execució del codi

Una vegada activat l'entorn virtual amb venv, executeu la següent ordre:

```sh
./src/carga_inicial.py
```

### Comprovació dels endpoints

Per a comprovar l'ús dels endpoint podeu utilitzar [Postman](https://www.postman.com/)
amb el fitxer proporcionat.
