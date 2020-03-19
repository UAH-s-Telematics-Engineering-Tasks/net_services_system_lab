<!-- # First steps with Asterisk

## Disclaimer
This info has been taken from asterisk's [wiki](https://wiki.asterisk.org/) unless otherwise noted.

## Runnig asterisk
You can run asterisk by invoking:

```bash
asterisk -cvvvvv # Run asterisk with a CLI attached and vervosity level 5
asterisk         # Run asterisk in the background. We can attach to it later on
astrisk -rvvvvv  # Attach a CLI to an already running asterisk instance 
```

Stoping it can by done by:

```bash
asterisk -rx 'core stop gracefully' # If not currently on asterisk's CLI
coder stop gracefully               # If on asterisk's CLI
```

Exiting the CLI is done by pressing `CTRL + C`.

### Running it as a service
In order to run it as a service you can get the following unit file into `/etc/systemd/system` and use `systemd`'s utilities with `systemctl`. Just be sure to correct file permissions on each of asterisk's dependencies as the user and group running the instance will be `asterisk:asterisk`. The file has been taken from [here](https://github.com/johannbg/systemd-units/blob/master/projects/asterisk/service/asterisk.service).

## Playing back an audio file
Asterisk uses **applications** to do stuff. We are going to use the `Playback()` app to play an audio file back to the caller when he/she dials `100`. To do so we need to take care of several things:

### Setting up `/etc/asterisk/extensions.conf`
The contents are not yeat crystal clear to me...

```ini
[from-internal]
exten = 100,1,Answer()
same = n,Wait(1)
; same = n,Playback(hello-world)
same = n,Playback(/home/vagrant/estefania)
same = n,Hangup()
```

We'll let asterisk anwswer the call and pplayback the provided file. If we use a standalone name asterisk will look for files under `/var/lib/asterisk/sounds/en/`. We can, as seen, provide absolute paths **without** the file extension. We can also see how the **SIP** clients should dial `100` to access this service.

Asterisk likes to play `.gsm` files. This audio codec provides us with low-quality compressed audio. The files can be generated from `.wav` files using good old `sox`. Just run:

```bash
sox input.xxx output.gsm
```

Where `xxx` is the input extension. You can then record any files you want and use them! Be careful though as converting a file to `.gsm` and back again introduces a great deal of noise...

### Adding users through `/etc/asterisk/pjsip.conf`
This file helps us define the transport protocol to use as well as *PBX* users:

```ini
[transport_udp]
type = transport
protocol = udp
; Bind (a.k.a listen on) to every interface
bind = 0.0.0.0

; Config extracted from https://wiki.asterisk.org/wiki/display/AST/Creating+SIP+Accounts
; Check https://wiki.asterisk.org/wiki/display/AST/PJSIP+Configuration+Sections+and+Relationships for info in user config!

; Templates for the necessary config sections

[endpoint_internal](!)
type = endpoint
context = from-internal
disallow = all
allow = ulaw

[auth_userpass](!)
type = auth
auth_type = userpass

[aor_dynamic](!)
type = aor
max_contacts = 1

; Instantiate those templates. If not overwritten the defaults are inherited!

[spike](endpoint_internal)
auth = spike_auth
aors = spike_aor
[spike_auth](auth_userpass)
username = spike
password = spike
[spike_aor](aor_dynamic)

[jin](endpoint_internal)
auth = jin_auth
aors = jin_aor
[jin_auth](auth_userpass)
username = jin
password = jin
[jin_aor](aor_dynamic)
```

A **SIP** client connecting to us should use the following data:
1. Username -> `spike`
2. Password -> `spike`
3. Server -> `Asterisk's Host IP`

You should see that the user registers itself automatically.

### Making the call
Depending on your **SIP** client you'll need to make the call in one way or another. I used Android's default phone app and had to manually ask it to use my **SIP** profile rather than the **SIM** card to make any calls. Be sure to be connected to the LAN where your asterisk instance is running!

### Differentiating called number, user and caller ID
When modifying `pjsip.conf` we are defining the accounts that any given softphone is going to use. We should note that the numbers we make the calls to are actually defined in `extensions.conf` through the so called extension number. That's where we map extension number to registered username. We can also add a caller ID that will be returned to the calling phone as additional info! -->

# Configurando una PBX con Asterisk

## Introducción
Se nos ha encargado configurar una centralita telefónica para comunicaciones **VoIP** esto es, para comunicaciones tanto de video como telefónicas soportadas sobre el protocolo de capa 3 **IP**. Para lograrlo emplearemos *Asterisk*, una implementación en *C* de una PBX de código libre.

Para lograr un mejor rendimiento y adecuar la instalación a nuestro sistema optaremos por compilar las fuentes nosotros mismos. Más adelante veremos las implicaciones de esta vía de acción.

Tras lograr instalar el programa llega el momento de configurarlo. La mayor parte de esta configuración se hará a través de archivos estáticos `.conf` que residen en `/etc/asterisk`. Llegado el momento comentaremos qué contiene cada uno e incluiremos en el documento los distintos archivos con comentarios acompañando las opciones escogidas. Seguiremos el mismo orden que cuando empezamos a poner todo en marcha para que exista un hilo conductor que cohesione el documento.

En aras de preparar un documento lo más completo posible comentaremos en un anexo los aspectos básicos del manejo de `asterisk` desde su propia interfaz por línea de comandos (`CLI`) y explicaremos cómo hemos preparado nuestro sistema para facilitar todo el desarrollo en la medida de lo posible. Comentaremos también los *softphones* que hemos utilizado para probar todo con el objetivo de facilitar la reproducibilidad de nuestro sistema.

Todos los archivos de configuración y scripts empleados durante la preparación de la PBX se pueden encontrar en un repositorio de [`GitHub`](https://github.com/) :octocat: público que nos ha facilitado la gestión de tantos archivos. Las rutas de los archivos que comentemos a lo largo del documento hacen referencia a ese mismo repositorio aunque también incluiremos enlaces directos a los archivos en cuestión ya que dada la longitud de según y qué archivos creemos que pueden dificultar el manejo de este informe.

## Instalando Asterisk
### Fuentes y dependencias
Al pretender instalar `asterisk` a partir de su código fuente primero debemos obtenerlo. Dado que nuestro escenario solo cuenta con un entorno basado en texto (en el anexo se comenta que nuestras máquinas se han levantado con `vagrant`) emplearemos siempre programas que se pueden invoccar desde una terminal sin depender de un entorno gráfico. La forma de distribuir estas fuentes suele ser a través de un archivo comprimido `tar.gz`. Por lo tanto debemos descargarlo y descomprimirlo. Este proceso se resume en las siguientes líneas que se encuentran en el script de automatización de instalación [`Asterisk_setup/Get_src_n_dependencies.sh`](https://github.com). Para lanzarlo basta con ejecutar `bash Get_src_n_dependencies.sh` desde la máquina en la que instalaremos el programa. Preferimos llamar explícitamente a la shell (con el comando `bash`) en vez de ejecutar el script con `./Get_src_n_dependencies.sh ` para evitar tenere que lidiar con los permisos de ejecución. Así nos evitamos un comando más (somos así de perezosos).


A medida que ha ido avanzando la cantidad de software desarrollado nos hemos visto obligados a escribir y utilizar librerías que nos faciliten el trabajo de manera que no tengamos que "reinventar la rueda" continuamente. Con `asterisk` no iba a ser de otra manera con lo que además de su código fuente debemos instalar las librerías de las que depende. En sistemas basados en `linux` se suele manejar el software instalado en unidades llamadas paquetes donde unos paquetes dependen de otros en la mayoría de los casos. Las librerías son el fondo paquetes normales y corrientes pero podemos instalarlas ya compiladas u obtener sus paquetes de desarrollo. Si instalamos las librerías compiladas a nivel de "usuario" permitimos que programas ya compilados puedan utilizar sus servicios pero este **NO** es nuestro caso... Nosotros necesitamos compilar las fuentes con las librerías (es decir, necesitamos "reolver los distintos `#include <...>` que aparecen en las fuentes de `asterisk`) por lo que necesitamos las fuentes de las librerías a su vez. En un sistema `Ubuntu` como el que estamos empleando estos paquetes suelen ir acompañados del sufijo `-dev`.

Sabemos que `asterisk` cuenta con un script que instala todas estas dependencias (`install_prereq.sh`) pero hemos preferido preparar el nuestro propio en un intento de entender qué hace cada dependencia y por qué es necesaria. Toda esta información se encuentra en el script de instalación antes mencionado.

Lo que hace el script de insatlación en definitiva es bajar las fuentes de `asterisk`, descomprimirlas y bajar las dependencias. Con todo esto ya estamos preparados para compilar este programa faraónico.

### Hora de compilar
Los desarrolladores de `asterisk` han pensado en nosotros al haber preparado un `Makefile`. `Make` es una herramienta de `GNU` que automatiza la compilación de cualquier tipo de proyecto. Antes de poder emplear este `Makefile` debemos cerciorarnos de cumplir todos los requisitos para instalar el programa para lo que ejecutamos el script `configure` navegando hasta `/usr/share/asterisk` (el lugar al que habíamos descomprimido las fuentes) y ejecutamos `./configure`. Si como esperamos todo está correcto podemos pasar a compilar el programa con tan sólo invocar `make`. Dada la extensión del programa y toda la funcionalidad que aporta es posible que no requiramos alguno de los módulos que se incorporan para trabajar. Para seleccionar qué cargar y qué no podemos ejecutar `make menuselect` para entrar en un menú gráfico basado en `ncurses` en el que escoger lo que usar. Tras decidirnos con correr `make install` tendremos `asterisk` instalado. Además del propio programa queremos tener una configuración de la que partir para tener una base sobre la que trabajar. Ejecutando `make samples`se copiaran configuraciones de ejemplo a `/etc/asterisk` para que podamos empezar a trabajar.

Con todo preparado nos queda ejecutar el propio programa. Teniendo la seguridad en mente hemos decidido ejecutar `asterisk` como un servicio de `systemd` para lo que hemos tenido que dar algún paso más. Todo aparece documentado en el anexo. A partir de ahora asumiremos que `asterisk` está corriendo en segundo plano. Pasamos pues a lanzar una terminal de `asterisk` para poder obtener información útil para la configuración.

## Primer contacto con `asterisk`
Con `asterisk` corriendo queremos lanzar una terminal contra la instancia en segundo plano, es decir, no queremos lanzar otro segundo proceso de `asterisk`. La mejor manera de obtener información acerca de un comando es consultar las páginas del manual de UNIX a través del comando `man`. Al hacerlo veremos que con la opción `-r` podemos conectarnos a instancias activas, justo lo que necesitamos. Además de esto podemos añadir una serie de `v`s para incrementar el nivel de verbosidad de la sesión que estamos a punto de abrir. La verbosidad no es más que el nivel de información que queremos recibir, a más verbosidad más 
detallada será la información que se nos devuelva. En nuestro caso hemos empleado un nivel de verbosidad de `5` con lo que el comando que emplearemos para abrir la sesión contra `asterisk` es `asterisk -rvvvvv`.

Tal y como hemos preparado nuestro sistema no podemos ejecutar directamente el comando anterior. Dado que el usuario que ha lanzado el daemon de `asterisk` es `asterisk` (a pesar de que tengan el mismo nombre son cosas totalmente distintas. Es común en sistemas UNIX emplear un nombre de usuario igual que el del ejecutable en cuestión. Debemos tener cuidado porque es muy fácil que esto nos confunda...) el usuario que puede conectarse es `asterisk`, no nostros. Al trabajar con `vagrant` el usuario con el que nos logueamos en la máquina es `vagrant` (ya estamos otra vez con nombres repetidos...) con lo que tendremos que ejecutar el comando como si fuéramos `asterisk`. A pesar de que muchos pensamos que el comando `su` solo sirve para iniciar una sesión como `root` nos permite ejecutar comandos como si fuéramos cualquier otro usuario. La opción `-c` nos permite incluir el comando a ejecutar y la opción `-l` indica el usuario a emplear para lanzazr el comando. Por tanto siempre que queramos conectarnos en nuestra máquina a la instancia de `asterisk` que está corriendo emplearemos: `su -c 'asterisk -rvvvvv' -l asterisk`. El comando anterior nos pedirá la contraseña del usuario `asterisk` (que en nuestro caso es `asterisk`, no somos muy de seguridad...) y ¡ya estaremos dentro!

En el anexo hemos comentado una serie de comandos básicos que nos permitiran trabajar de una manera más cómoda. Siendo capaces de interactuar de forma directa con `asterisk` pasamos a comentar las diferentes "piezas" que lo componen para después empezar a hablar de configuraciones.

## Diseccionando `astrisk`
### Registrando usuarios
A pesar de darlo muchas veces por sentado las centralitas cuentran con clientes que en algún momento deben haberse vinculado. Este proceso es lo que se conoce como *registro* en el contexto de la telefonía *VoIP* y las entidades que se registran se denominan *endpoints* y pueden ser de `3`tipos:

- **Peer**: Solamente podrá recibir llamadas
- **User**: Solamente hace llamadas
- **Friend**: Auna ambas funcionalidades

En nuestro caso trabajaremos principalmente con *friends* pero llegado el momento trabajaremos con un par de *peers* que se encargarán de atender las llamadas de unas colas de servicio.

`Asterisk` internamente maneja canales de comunicación que abre según se requieran. Al hacer una llamada es el llamante el que crea un primer canal hasta `asterisk` y es `asterisk` el que crea un segundo canal con el llamado para después conectar ambos de manera que se pueda cursar la llamada. Los llamados *channel drivers* se encargan de crear y gestionar estos canales en función de la tecnología subyacente. En el contexto de la telefonía *IP* empleamos el protocolo **SIP** (**S**ession **I**nitiation **P**rotocol) con lo que nos encargaremos de configurar un *SIP Channel Driver*.

`Asterisk` cuenta con 2 manejadores **SIP**, `res_pjsip` y `chan_sip`. El primero es más moderno y la mayor parte del código fuente no es nativo de `asterisk` ni ha sido desarrollado por la gente de *Digium*. El segundo está *deprecado* (se acabará eliminando en posteriores versiones) pero nos ha resultado más sencillo trabajar con él. Nuestro caso de uso es relativamente particular en el sentido de que estamos constantemente cambiando de red de área local y los teléfonos registrados así como la propia configuración. Constantemente nos encontramos registrando nuevos usuarios y desregistrando a otros con la que la facilidad para hacer este proceso es muy importante. Si bien `res_pjsip` es más moderno las herramientas que nos brinda la **CLI** de `asterisk` para manejar `chan_sip` nos han resultado más intuitivas con lo que hemos optado por emplear este segundo manejador.

Dado que la versión de `asterisk` con la que hemos trabajado es la `17` hemos tenido que cambiar `res_pjsip` que venía incluido de manera nativa por el antiguo `chan_sip`. Para ello hemos tenido que modificar el archivo `modules.conf` con las siguientes líneas:

```ini
; Remove res_pjsip and make way for good old chan_sip
load => chan_sip.so
noload => res_pjsip.so
```

Recargando la instancia de `asterisk` para que se plasmaran los cambios veremos cómo hemos cambiado el manejador **SIP**. Podemos comprobarlo ejecutando el comando `sip show peers` y viendo que se nos devuelve una lista por ahora vacía.

Ahora ha llegado el momento de generar una serie de usuarios contra los que se podrán registrar los distintos terminales. Para ello tenemos que trabajar con el archivo `sip.conf` y añadir al final del mismo lo siguiente:

```ini
; Friend template
[friends_internal](!)
type=friend
host=dynamic
context=from-internal
disallow=all
allow=ulaw ; Audio codec
allow=h264 ; Video codec

; Template instances
[alice](friends_internal)
secret=alice

[pablo](friends_internal)
secret=pablo
language=es
```

Debemos empezar por dejar claro que el extracto de la configuración que hemos incluido se apoya en opciones por defecto que ya existían en la docuentación generado con `make samples` durante la instalación. El modo de transporte para los clientes configurados es `UDP` y hemos puesto as `asterisk` a "escuchar" en todas las interfaces a través de la opción:

```ini
udpbindaddr=0.0.0.0
```

El primer bloque de configuración se corresponde con una plantilla o template para usuarios de un mismo tipo (de ahí el `(!)` final). En ella declaramos que los clientes de tipo `friends_inetrnal` son `friends` (pueden iniciar y recibir llamadas) y que emplearán la [*Ley-Mu*](https://en.wikipedia.org/wiki/G.711#%CE%BC-law) para codificar el audio (`allow=ulaw`) y el códec `H.264` para el video. Antes de estas dos opciones hemos deshabilitado todos los demás códecs con `disallow=all` para evitar posibles colisiones. Cabe destacar que si bien `asterisk` puede traducir códecs de audio entre clientes que empleen dos distintos no es capaz de hacer lo mismo con el vídeo, cosa que debemos tener en cuenta al configurar las videollamadas. El contexto del usuario por ahora carece de sentido pero lo explicaremos al comentar el plan de marcación que se incluye en `extensions.conf`. Por ahora debemos saber que el contexto de estos usuarios es `from-internal`.

Además de estas opciones hemos declarado que el host asociado a estos usuarios es dinámico. En vez de saber que una IP específica se va a registrar contra estos usuarios dejamos que sea el usuario el que se registre desde cualquier dirección. Es importante señalar que somos capaces de desregistrar estos usuarios para evitar conflictos de manera automática empleando el comando `sip unregister <nombre_de_usuario>` desde la **CLI** de `asterisk`. El proceso de registro varía en función del softphone que se emplee. En nuestro caso hemos usado *linphone* en teléfonos *android*. Para este sistema tenemos que emplear una cuenta **SIP** e introducir nuestro usuario y contraseña (lo vemos en un momento) además de la IP de la máquina ejecutando `asterisk` (lo podemos consultar ejecutando `ip a` desde una shell normal en la misma). Debemos emplear **UDP** en la capa de transporte tal y como comentábamos más arriba dada nuestra configuración. Para nuestro escenario emplear **UDP** no supone un inconveniente ya que no buscamos una calidad de servicio extrema y conseguimos trabajar sobre una base más liviana y menos exigente.

Empleando la plantilla anterior instanciamos dos usuarios cuyos nombres de usuario y contraseña son `pablo/pablo` y `alice/alice` (ya dijimos que la seguridad no era lo nuestro...). Dado que asterisk es capaz de reproducir mensajes de audio a los usuarios podemos configurar un idioma para cada uno. De no hacerlo se utilizará el inglés como estándar. Esto cobrará importancia al instalar archivos de audio de otros idiomas más adelante. Por ahora basta con saber que el idioma que se empleará para `pablo` es espñol en vez de inglés.

Con los usuarios configurados es momento de empezar a dotar a nuestra PBX de funcionalidad a través del archivo de maración.

### La primera llamada
