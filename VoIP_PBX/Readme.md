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
Los desarrolladores de `asterisk` han pensado en nosotros al haber preparado un `Makefile`. `Make` es una herramienta de `GNU` que automatiza la compilación de cualquier tipo de proyecto. Antes de poder emplear este `Makefile` debemos cerciorarnos de cumplir todos los requisitos para instalar el programa para lo que ejecutamos el script `configure` navegando hasta `/usr/share/asterisk` (el lugar al que habíamos descomprimido las fuentes) y ejecutamos `./configure`. Si como esperamos todo está correcto podemos pasar a compilar el programa con tan sólo invocar `make`. Dada la extensión del programa y toda la funcionalidad que aporta es posible que no requiramos alguno de los módulos que se incorporan para trabajar. Debemos prestar atención e incluir todos los módulos para trabajar con conectores **ODBC** (los explicaremos más adelante). Por defecto están todos incluidos. Para seleccionar qué cargar y qué no podemos ejecutar `make menuselect` para entrar en un menú gráfico basado en `ncurses` en el que escoger lo que usar. Tras decidirnos con correr `make install` tendremos `asterisk` instalado. Además del propio programa queremos tener una configuración de la que partir para tener una base sobre la que trabajar. Ejecutando `make samples`se copiaran configuraciones de ejemplo a `/etc/asterisk` para que podamos empezar a trabajar.

Con todo preparado nos queda ejecutar el propio programa. Teniendo la seguridad en mente hemos decidido ejecutar `asterisk` como un servicio de `systemd` para lo que hemos tenido que dar algún paso más. Todo aparece documentado en el anexo. A partir de ahora asumiremos que `asterisk` está corriendo en segundo plano. Pasamos pues a lanzar una terminal de `asterisk` para poder obtener información útil para la configuración.

## Primer contacto con `asterisk`
Con `asterisk` corriendo queremos lanzar una terminal contra la instancia en segundo plano, es decir, no queremos lanzar otro segundo proceso de `asterisk`. La mejor manera de obtener información acerca de un comando es consultar las páginas del manual de UNIX a través del comando `man`. Al hacerlo veremos que con la opción `-r` podemos conectarnos a instancias activas, justo lo que necesitamos. Además de esto podemos añadir una serie de `v`s para incrementar el nivel de verbosidad de la sesión que estamos a punto de abrir. La verbosidad no es más que el nivel de información que queremos recibir, a más verbosidad más 
detallada será la información que se nos devuelva. En nuestro caso hemos empleado un nivel de verbosidad de `5` con lo que el comando que emplearemos para abrir la sesión contra `asterisk` es `asterisk -rvvvvv`.

Tal y como hemos preparado nuestro sistema no podemos ejecutar directamente el comando anterior. Dado que el usuario que ha lanzado el daemon de `asterisk` es `asterisk` (a pesar de que tengan el mismo nombre son cosas totalmente distintas. Es común en sistemas UNIX emplear un nombre de usuario igual que el del ejecutable en cuestión. Debemos tener cuidado porque es muy fácil que esto nos confunda...) el usuario que puede conectarse es `asterisk`, no nostros. Al trabajar con `vagrant` el usuario con el que nos logueamos en la máquina es `vagrant` (ya estamos otra vez con nombres repetidos...) con lo que tendremos que ejecutar el comando como si fuéramos `asterisk`. A pesar de que muchos pensamos que el comando `su` solo sirve para iniciar una sesión como `root` nos permite ejecutar comandos como si fuéramos cualquier otro usuario. La opción `-c` nos permite incluir el comando a ejecutar y la opción `-l` indica el usuario a emplear para lanzazr el comando. Por tanto siempre que queramos conectarnos en nuestra máquina a la instancia de `asterisk` que está corriendo emplearemos: `su -c 'asterisk -rvvvvv' -l asterisk`. El comando anterior nos pedirá la contraseña del usuario `asterisk` (que en nuestro caso es `asterisk`, no somos muy de seguridad...) y ¡ya estaremos dentro!

En el anexo hemos comentado una serie de comandos básicos que nos permitiran trabajar de una manera más cómoda. Siendo capaces de interactuar de forma directa con `asterisk` pasamos a comentar las diferentes "piezas" que lo componen para después empezar a hablar de configuraciones.

## Funcionalidad de una PBX básica
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

Con todo listo y los usuarios registrados podemos comprobar que todo ha ido correctamente ejecutando `sip show peers` en la **CLI** de `asterisk` y viendo que los usuarios registrados cuentan con una *IP* (la de su terminal) en la columna `host`.

Con los usuarios configurados es momento de empezar a dotar a nuestra PBX de funcionalidad a través del archivo de maración.

### Hola mundo y la primera llamada
Acostumbrados a asociar un número de teléfono con cada usuario en la red telefónica tradicional debemos dejar claro que esta relación **NO** se establece al configurar los usuarios en `sip.conf`. Si nos fijamos veremos que no hemos hablado de ningún número hasta ahora. La lógica de la centralita se condensa en el archivo `extensions.conf` que tiene una sintaxis muy particular. En él definimos los números (extensiones) a las que podemos llamar desde cualquier terminal que cuente con un usuario registrado. De aquí en adelante siempre que hablemos de terminal damos por sentado que se ha configurado un usuario y que se encuentra registrado. Especificamos también las acciones que llevar a cabo ante una llamada a través de las llamadas [*dialplan applications*](https://wiki.asterisk.org/wiki/display/AST/Asterisk+17+Dialplan+Applications). La sintaxis que siguen las reglas es una de las siguientes: 

```ini
; Formato 1
extension => número_extensión, prioridad, aplicación_a
extensión => número_extensión, prioridad + 1, aplicación_b

; Formato 2
extension => número_extensión, prioridad, aplicación_a
    same => prioridad + 1, aplicación_b
```

Señalamos que la primera prioridad deber ser `1` y que en las reglas siguientes debemos ir incrementando la prioridad en `1` unidad o incluir directamente la prioridad `n` que incrementa esta prioridad de 1 en 1 de forma implícita. Además de números de extensión estáticos podemos incluir también reglas con comodines que coincidad con una serie de números en base a unas reglas bien definidas.

Una aplicación muy sencilla que simplemente reproduce un mensaje al llamante cuando se llama al número `100` sería:

```ini
[from-internal]
; Hello World (a.k.a General Tests)
exten => 100,1,Answer()                 ; Asterisk descuelga el la línea
    same => n,Wait(1)                   ; Espera 1 segundo para dar tiempo al terminal a prepararse
    same => n,Playback(hello-world)     ; Reproduce un mensaje de vuelta al llamante
    same => n,Wait(1)                   ; Espera 1 segundo para no cortar el final del mensaje
    same => n,Hangup()                  ; Cuelga la llamada
```

Nótese que hemos eliminado una línea que accede a una base de datos ya que no nos aporta nada por ahora. Se han explicado las aplicaciones empleadas con comentarios a su lado. Además 
llamamos la atención al contexto bajo el que se encuadra la extensión que incluimos que no es otro que el que señalábamos al definir los usuarios de nuestra centralita, `from-internal`. Todas las extensiones que describamos a partir de ahora pertenecen a este contexto a no ser que se explicite lo contrario. Así conseguimos ser lo más fieles posbles a la configuración real que se encuentra en los archivos de este repositorio. Finalmente señalamos que el parámetro que le pasamos a la aplicación [`Playback()`](https://wiki.asterisk.org/wiki/display/AST/Asterisk+17+Application_Playback) es un archivo de audio (sin la extensión) que se encuentra en los directiorios `/var/lib/asterisk/sounds/<idioma>` donde `<idioma>` puede ser `en` o `es` para inglés y español respectivamente entre otras.

Por ahora nos centraremos en la forma de hacer una llamada normal a través de la aplicación [`Dial()`](https://wiki.asterisk.org/wiki/display/AST/Asterisk+17+Application_Dial). Aprovecharemos también para incluir los conceptos de variables globales y subrutinas además de mostrar un ejemplo de extensiones con comodines:

```ini
[globals]
; Extension <--> Peer Mappings
200=alice
201=pablo
202=foo
203=foodb

[from-internal]
; User calls!
exten => _2XX,1,Set(peer_name=${GLOBAL(${EXTEN})})                  ; Asigna un valor determinado a la variable 'peer_name'
    same => n,GotoIf($["${peer_name}" = ""]?wrong_peer,1)           ; Si la extensión llamada no corresponde a nadie salta a la extensión 'wrong-peer'
    same => n,gosub(store-data,s,1,(${EXTEN}))                      ; Antes de llamar llama a la subrutina 'store-data'
    same => n,Dial(SIP/${peer_name},10,tm(native-random))    ; Llama al usuario requerido
    same => n,VoiceMail(${EXTEN})                                   ; Si no coge la llamada dejamos un mensaje de voz

exten => wrong_peer,1,Verbose(2,Called a wrong peer...)             ; Escribe en la CLI un mensaje
    same => n,Playback(tt-weasels)                                  ; Reproduce el audio
    same => n,Wait(1)                                               ; Espera 1 segundo para finalizar la reproducción suavemente
    same => n,Hangup()                                              ; Cuelga el canal

; Sotore charging data in appropriate DBs
[store-data]
exten => s,1,Verbose(${ODBC_SQL(INSERT INTO call_data (caller_id, called_exten) VALUES (\"${CALLERID(all):4:-1}\", ${ARG1}))})  ; Inserta datos en una DB
    same => n,AGI(update_mongo_db.py,${GLOBAL(${ARG1})})                                                                        ; Llama a un script externo
    same => n,Return()                                                                                                          ; Vuelve a la extensión que nos llamó
```

A pesar de que parece que la extensión es muy complicada veremos cómo en realidad no es nada más que un tema de orden. La extensión `_2XX` es un patrón (empieza con `_`) que coincide con los números en el intervalo `[200, 299]`, es decir, `X` sustituye a un dígito cualquiera. Nada más entrar por esta extensión fijamos el valor de una variable para este canal, `peer_name`. En vez de tener que reescribir esta extensión para cada usuario hemos creado una zona de variables globales (justo debajo de `[globals]`) que nos permite traducir los valores numéricos a nombres de usuario. Cada canal tiene una serie de [variables básicas](https://wiki.asterisk.org/wiki/display/AST/Asterisk+Standard+Channel+Variables) que podemos emplear para obtener información. Lo único que hacemos es obtener el valor de la variable global que identificamos con la extensión que ha sido llamada. En el plan de marcación accedemos al valor de variables a través del "operador" `${}` con lo que `${EXTEN}` nos devuelve el valor de la extensión marcada. La "función" `GLOBAL(X)` nos devuelve el valor de la variable global identificada por `X` y asignamos al valor a la variable del canal que definimos con el operador `${}` de nuevo (sí, la sintaxis es bastante fea).

En caso de que este identificador no se encuentre en el área de variables globales `GLOBAL(X)` devolverá una cadena vacía (`""`) con lo que podemos usarlo de condición en un salto condicional. Si la condición se cumple saltaremos a una extensión preparada para manejar la situación y simplemente colgar al llamante tras informarle de que unas comadrejas se han comido el equipo telefónico... En caso contrario llamamos a la subrutina `store-data` yendo a su extensión `s` y prioridad `1`. Nótese que esta subrutina es en el fondo otro contexto distinto a `[from-internal]`, las rutinas y macros en el plan de marcación son sus "propios" contextos tal y como veremos al comentar la emulación de un call center. Además pasamos la extensión llamada como argumento ya que el salto implica un cambio de extensión al fin y al cabo y si no no podríamos recuperarla... En la subrutina primero introducimos unos datos en la base de datos *MySQL* y luego llamamos a un script que interacciona con una base de datos *MongoDB* pra luego volver al punto en el que estábamos. Explicaremos estas aplicaciones en profundidad más adelante.

De nuevo en la extensión inicial nos limitamos a llamar al usuario que habíamos obtenido antes durante un periodo máximo de `10` segundos. Además permitimos al llamado redireccionar la llamada con la opción `t` (más adelante lo comentaremos) y reproducimas música de la clase `native-random` al llamado a través de la opción `m`. En breve comentaremos qué es esto de las clases de música.

Si el llamado no contesta en `10` segundos entonces pasamos a ejecutar la siguiente aplicación que permitirá al llamante dejar un mensaje de voz en el buzón asociado a la extensión llamada. Pasamos a hora a comentar la configuración y uso de estos buzones de voz.

Con todo hemos cubierto bastante terreno con esta extensión que si bien podría ser más sencilla hemos sido capaces de afinar su funcionamiento haciendo uso de vairas caractarísticas del propio plan de marcación.

### Utilizando buzones de voz
Antes hemos visto cómo dejar mensajes en los buzones de voz con lo que solo necesitamos saber cómo se configuran y como puede cualquier usuario acceder a ellos. La configuración es muy sencilla y se hace a través del archivo `voicemail.conf`. Tan solo debemos configurar entradas como:

```ini
[default]
200 => 123, Alice, foo@foo
201 => 123, Pablo, foo@gmail.com
202 => 123, Foo, vagrant@localhost
203 => 123, FooDB, vagrant@localhost
```

Así, el buzón de voz asociado a la extensión `200` tiene la contraseña `123` para acceder, pertenece a `Alice` y las notificaciones pertinentes por correo se enviarán a `foo@foo`. La idea es idéntica para los demás casos y es la extensión definida en este documento la que se emplea al invocar a la aplicación [`VoiceMail()`](https://wiki.asterisk.org/wiki/display/AST/Asterisk+17+Application_VoiceMai) del plan de marcaciones. Si somos estrictos deberíamos pasar como argumento a `VoiceMail()` la cadena `extension@mail_context` donde `mail_context` es `default` en nuestro caso. No obstante si se omite esta segunda parte se supone que el contexto es en efecto `default` con lo que nos podemos ahorrar incluirlo. Dado que este documento es público hemos ocultado la dirección de correo veraz de *gmail* pero señalamos que los correos se envian de manera correcta. Tan solo hemos tenido que instalar en el sistema el programa `sendmail` (en sistemas basados en debian basta con ejecutar `sudo apt install sendmail`) ya que es el que emplea `asterisk` para enviar correos tal y como aparece recogido en la opción `mailcmd` del mismo archivo. El resto de las opciones que hemos empleado eran las que venían por defecto. Destacamos que los correos que nos llegan continen como adjunto el mensaje de voz.

Solo nos queda habilitar una extensión para que los usuarios puedan escuchar sus mensajes. En `extensions.conf` hemos incluido:

```ini
; Access left Voice Messages
exten => 400,1,VoiceMailMain()  ; Lanza el contestador
    same => n,Hangup()          ; Cuelga la llamada al acabar
```

Llamando a la extensión `400` simplemente se invoca una aplicación automatizada que le requerirá a cada usuario el número de su buzón de voz (extensión asociada) y la contraseña definida en `voicemail.conf`. Tras ello se entra en un menú guiado.

Si bien podía parecer intimidante en un principio hemos visto que configurar los buzones de voz ha sido relativamente sencillo. Pasamos a comentar las llamadas en grupo.

### Llamadas en grupo
Si pensamos en el modelo de canales que discutíamos anteriormente donde `asterisk` unía canales entre los usuarios y él a través de puentes o `bridges` si queremos conectar a varios usuarios a la vez solo tendríamos que unir más de dos canales en un mismo bridge. Esto es "exactamente" lo que hace la aplicación [`ConfBridge()`](https://wiki.asterisk.org/wiki/display/AST/Asterisk+17+Application_ConfBridge) del plan de marcación. Podemos lograr que todo aquel que llame a la extensión `500` se una a esta llamada grupal con tan solo declarar:

```ini
; Group Calls
exten => 500,1,Answer()                     ; Asterisk descuelga la llamada
    same => n,ConfBridge(foo-conference)    ; Y nos metemos en la sala de conferencias
```

Cada usuario que llame a esta extensión se unirá a la "salsa de conferencias" `foo-conference` y estará comunicado con todos los demás participantes. Si bien es cierto que esta extensión es totalmente funcional no estamos empleando ninguno de los parámetros adicionales que nos ofrece esta aplicación y que nos permitirían añadir música de espera si se es el único asistente o requerir una contraseña para acceder. Todo esto se puede configurar en el archivo `confbridge.conf`.

### Redirección de llamadas
Si recordamos el significado de la opción `t` en la aplicación `Dial()` veremos que permitía al llamado redireccionar las llamadas en función de lo establecido en el archivo `features.conf` tan solo necesitamos ver un par de líneas de este archivo para explicar en qué consiste esta redirección de llamadas:

```ini
[featuremap]
blindxfer => #1
atxfer => *2
```

En estas dos líneas definimos las teclas que se deben marcar durante una llamada para llevar a cabo cada uno de los tipos de redirección de llamada posibles:

- Redirección "ciega" (*blindxfer*) -> En estas trasnferencias o redirecciones la parte que redirecciona (el llamado en nuestro caso) se desconecta de la llamada tan pronto como se lleve a cano esta redirección. Simplemente se desvía al llamante a otra extensión y nos "olvidamos".

- Redirección supervisada (*atxfer*) -> En este caso la parte que redirecciona contacta con la extensión destino de antemano para cerciorarse de que está preparada para atender al usuario que estamos a punto de enviar para allá.

Tal y como se recoge en el archivo anterior el llamado solo tiene que pulsar `#1` o `*2` durante la llamada para llevar a cabo cualquiera de los dos tipos de redirecciones. Recordamos que para que esto surta efecto debe estr activada la opción `t` en la llamada a `Dial()`. Si además queremos dotar al llamante de esta capacidad de redirección debemos pasar también la opción `T` a `Dial()`.

Si nos paramos a analizarlo tampoco ha resultado muy difícil empezar a funcionar con las redirecciones activadas. Ahora ha llegado el momento de hablar de la música en espera.

### Música en espera
Si bien lo más común al llamar a otra persona es escuchar los característicos pitidos a los que nos hemos acostumbrado con la red telefónica tradicional no podemos decir lo mismo de cuando estamos en una cola de espera para ser atendidos por ejemplo. En este segundo caso es común que se reproduzca una música en espera, que sule ser entre un poco y bastante irritante, interrumpida por mensajes que nos informan de la gente que tenemos por delante en la cola u otro tipo de mensajes. Las centrlitas tradicionales suelen estar reproduciendo esta música en espera de manera continua lo que supone un malgasto de recursos, pero `asterisk` solo lo hace cuando es necesario. Si bien esto no nos afecta deirectamente es curioso ver cómo `asterisk` ha dado solución a alguna que otra mala práctica en la implementación de este tipo de sistemas.

La configuración de esta música de fondo se maneja a través del archivo `musiconhold.conf` en el que aparecen definidas varias clases de música en espera en función de las fuentes de audio, la política de reproducción las interjecciones... En nuestro caso hemos empleado una configuración prácticamente idéntica a la que proveía la instalación:

```ini
[default]
mode=files
directory=moh

[native-random]
mode=files
directory=moh
announcement=queue-thankyou
sort=random
```

Tenemos dos perfiles, `default` y `native-random` que residen bajo el contexto `[general]`. Ambos reproducen archivos que se encuentran en `/var/lib/asterisk/moh` mientras que la segunda clase varía estos archivos de manera aleatoria y reproduce la interjeción `queue-thankyou` a intervalos regulares. En el primer caso el orden de reproducción de los archivos es indefinido al no haberse especificado.

A pesar de que dadas las opciones podemos pensar que la segunda clase solo es aplicable a colas de espera vemos que `asterisk` no impone restricción alguna tal y como demostramos en la extensión que se encarga de manejar las llamadas. Si observamos la clase que definimos para la música en espera en vez de el pitido (`m(native-random)`) es justo este segundo perfil y no existe problema alguno. Esto nos permite hacernos una idea de la versatilidad de este sistema.

Si queremos añadir más canciones en espera no tenemos más que añadirlas directamente a `/var/lib/asterisk/moh` o crear un nuevo directorio y apuntar la opción `directory` al mismo. Disponemos de la herramienta `sox` que se autodenomina la navaja suiza del audio que nos permite convertir archivos de audio fácilmente a formatos soportados como `.gsm` y `.sln16` entre otros.

Observamos lo fácil que es darle un toque personal a `asterisk` a través de una buena selección de música. Veamos como añadir voces y muestras de audio en otros idiomas.

### Internacionalizando nuestra centralita
Antes habíamos comentado cómo `asterisk` buscaba los archivos de audio que le pasábamos a `Playback()` en `/var/lib/asterisk/sounds/<idioma>`. Con tan solo crear otras carpetas con nombres diferentes y "rellenarlas" con muestras en el idioma elegido habremos "instalado" un nuevo idioma. Podemos poner los códigos de idioma que queramos nosotros sin problema siempre que seamos coherentes con lo configurado en `sip.conf`. Podemos incluir las muestras en español por ejemplo en `i_guess_this_is_spanish` pero hemos decidido ser tradicionales y emplear nombres comunes como `es`. Si navegamos a [`Asterisk Sounds`](https://www.asterisksounds.org/en/download) encontraremos muestras para varios idiomas. Con tan solo bajarlas y descomprimirlas en el lugar adecuado ya tenemos el trabajo hecho. Además de los archivos en español también añadimos los archivos "extra" en inglés para tener acceso a todas las muestras que pudieramos necesitar y probar así a añadir archivos de audio, no solo instalarlos desde 0.

Para facilitar el proceso hemos automatizado la descarga, descompresión y limpieza en un pequeño script que se encuentra en `Asterisk_setup` y se llama `Install_es_n_extra_audio.sh`. Al igual que con el script de instalación de dependencias basta con ejecutar `bash Install_es_n_extra_audio.sh`. El contenido del archivo es:

```bash
#!/bin/bash

# Get the files from asterisksounds.org
    # Extra English audio files
    sudo wget -O /var/lib/asterisk/sounds/en/extra-en.zip https://www.asterisksounds.org/sites/asterisksounds.org/files/sounds/en/download/asterisk-sounds-extra-en-2.9.15.zip

    # Make the directory for Spanish Audio
    sudo mkdir /var/lib/asterisk/sounds/es

    # Get both file packages
    sudo wget -O /var/lib/asterisk/sounds/es/core-es.zip https://www.asterisksounds.org/sites/asterisksounds.org/files/sounds/es-ES/download/asterisk-sounds-core-es-ES-2.9.15.zip
    sudo wget -O /var/lib/asterisk/sounds/es/extra-es.zip https://www.asterisksounds.org/sites/asterisksounds.org/files/sounds/es-ES/download/asterisk-sounds-extra-es-ES-2.9.15.zip

# Uncompress everything and clean up!
sudo unzip /var/lib/asterisk/sounds/*/*.zip
sudo rm /var/lib/asterisk/sounds/*/*.zip

# Fix permissions for both languages
sudo chown -R asterisk:asterisk /var/lib/asterisk/sounds
```

Fijémonos en cómo debemos actualizar los permisos de los archivos ya que al ejecutar los comandos de descompresión como `root` (hemos añadido `sudo` ya que este directorio **NO** pertenece al usuario `vagrant` sino a `asterisk`) pertenecen a `root` y `astrisk` sería incapaz de abrirlos... Con tan solo ejecutar lo anterior ya estaría todo listo y funcionando. ¡Solo nos queda comentar la macro que emula un call center para terminar de describir el funcionamiento de una PBX básica!

### Emulando un Call Center
Si pensamos en lo que es en realidad un *call-center* observaremos que no es más que un "menú" que acaba haciendo una llamada a un usuario específico en función de cómo lo recorramos. Sabiendo que contamos con saltos a distintas extensiones y prioridades podemos en cierto modo controlar el flujo de ejecución del plan de marcación con lo que conseguimos emular un menú como el que necesitamos. Para hacerlo definimos un nuevo contexto (`call-center-menu`) que nos permita independizar el punto de entrada del propio menú (reocordemos que los usuarios solo pueden marcar extensiones del contexto `[from-internal]`). Así, en el plan de marcación tan solo debemos incluir una nueva extensión que salte a este nuevo contexto. En definitiva hacemos un salto controlado a otro lugar, igual que cuando un proceso pide un servicio al *OS* provocando para ello un *trap*.

Una vez lleguemos al menú en cuestión interactuamos con el usuario a través de la reproducción de muestras de voz. La entrada de este usuario son marcaciones del teclado con lo que tenemos que emplear aplicaciones que sean capaces de leerlas para poder luego interpretarlas. Para ello emplearemos la aplicación [`Background()`](https://wiki.asterisk.org/wiki/display/AST/Asterisk+17+Application_Background) que reproduce un archivo de audio a la espera de una extensión a la que saltar que se puede introducir durante la reproducción. Si bien el resultado final es parecido al de [`Goto()`](https://wiki.asterisk.org/wiki/display/AST/Asterisk+17+Application_Goto) la forma de lograr el resultado es totalmente distinta. En caso de que el usuario escuche todo el mensaje reproducido por `Background()` contamos con la aplicación [`WaitExten()`](https://wiki.asterisk.org/wiki/display/AST/Asterisk+17+Application_WaitExten) que esperará hasta que el usuario introduzca una extensión en cuestión.

Solo nos queda comentar la capacidad que tenemos de asociar nombres a prioridades con el objetivo de poder saltar a ellas. Si tenemos una prioridad `n` en una extensión podemos emplear la sintaxis `n(foo)` para asociar el nombre `foo` con dicha prioridad para poder referirnos a ella más adelante.

Tomando ventaja de todo lo anterior llegamos aun menú como éste definido en `extensions.conf`:

```ini
; Call Center Menu
exten => 600,1,Goto(call-center-menu,s,1)

; Call center menu
[call-center-menu]
exten => s,1,Answer()                                               ; Descuelga la llamada. ¡Solo habíamos saltado aquí!
    same => n(main),Background(press-1&or&press-2)                  ; Reproduce los mensajes del argumento
    same => n,WaitExten()                                           ; Espera a una extensión

exten => 1,1,Playback(you-entered)                                  ; Reproduce la muestra del argumento
    same => n,SayNumber(1)                                          ; Reproduce un mensaje que diga el número del arguemento
    same => n(maina),Background(press-3&or&press-4&or&vm-helpexit)  ; Análogo a la llamda a Backgournd() aterior
    same => n,WaitExten()                                           ; Análogo a la extensión s

exten => 2,1,Playback(you-entered)
    same => n,SayNumber(2)
    same => n,Playback(vm-goodbye)
    same => n,Wait(1)
    same => n,Hangup() 

exten => 3,1,Playback(spy-agent)
    same => n,goto(s,main)                                          ; Volvemos al menu principal de la extensión s

exten => 4,1,Playback(hello-world)
    same => n,Dial(SIP/pablo)                                       ; Acabamos llamando a 'pablo' SIN poder dejar mensajes de voz

exten => #,1,Playback(vm-goodbye)
    same => n,Hangup()                                              ; Simplemente colgamos la llamada
```

La idea principal es saltar a las extensiones que se vayan introduciendo durante las llamadas a `Background()` o `WaitExten()` y controlar el flujo del menú en función de los mensajes que vamos reproduciendo al usuario. Cabe destacar, a modo de curiosidad, que para reproducir varios mensajes con una sola llamada a `Background()` debemos concatenarlos con el símbolo `&`. La sintaxis de `asterisk` sí que es horrible...

Con todo documentado podemos abordar el elefante en la habitación: la interconixión de `asterisk` con bases de datos externas a través de conectores **ODBC** (**O**pen **D**ata**B**ase **C**connectors).

## Un paso más allá: Interconexión con sistemas externos
Por ahora solo nos las hemos visto con el propio `asterisk`. Uno de los porblemas que esto conlleva es lo estático de las configuraciones. Es decir, una vez que modifiquemos los usuarios de la centralita debemos volver a cambiar el archivo para cambiar sus características o aceptar terminales nuevos por ejemplo. Para intentar dotar a nuestro sistema de un grado más de dinamismo podemos intentar aprovechar la arquitectura de tiempo real de `asterisk` o [**ARA**](https://wiki.asterisk.org/wiki/display/AST/Realtime+Database+Configuration) que nos permite introducir nuevos usuarios a través de una base de datos externa.

Por tanto nuestro objetivo principal es agregar usuarios dinámicamente a través de una base de datos. Teniendo esto siempre en mente vamos a ir relatando los pasos que debemos seguir para cumplir nuestro objetivo.

### Cargando usuarios desde una base de datos
Con el objetivo de facilitar la configuración de la base de datos externa a la vez que contar con mucha documentación que nos respalde hemos decidido emplear una base de datos relacional `MySQL`. Instalarla en un sistema basado en `Debian` es tan sencillo como ejecutar `sudo apt install mysql-server`. Podemos comprobar que tras la insrtalación todo está funcionando de manea correcta si ejecutamos `systemctl status mysql`. Debmos señalar que `MySQL` no es la propia base de datos en sí sino un sistema gestor de bases de datos que puede manejar varias a la vez. Nosotros hemos decidido ser poco originales y crear la base de datos `asterisk` para trabajar con la centralita. Hemos establecido además un usuario específico para que `asterisk` pueda comunicarse únicamente con la base de datos para la que debe tener acceso y como no podía ser de otra manera lo hemos llamado `asterisk` también.

Para crear este usuario primero debemos iniciar una sesión como `root` en la consola de `mysql` ejecutando `sudo mysql -u root -p` y pulsando enter desde la propia shell. Dentro debemos ejecutar las siguientes órdenes para crear a este usuario así como la base de datos `asterisk`:

```sql
CREATE USER 'asterisk'@'localhost' IDENTIFIED BY 'asterisk';    -- Crea el usuario asterisk con contraseña asterisk
CREATE DATABASE asterisk;                                       -- Crea la base de datos asterisk
GRANT ALL PRIVILEGES ON asterisk.* TO 'asterisk'@'%';           -- Otorga los permisos necesarios al usuario asterisk en la DB asterisk
quit;
```

A partir de ahora podemos manejar la base de datos iniciando sesión en el servidor de `mysql` con cualquiera de los dos usuarios. Si queremos entrar como `asterisk` el comando a aejecutar será `mysql -u asterisk -p`. Tan solo debemos introducir la contraseña anterior cuando se requiera. Ahora debemos darnos cuenta de que si `asterisk` puede obtener información de estas bases de datos entonces esperará recibirla a través de unas tablas bien definidas. Navegando por la wiki de `asterisk` llegamos a una de estas descripciones [aquí](https://wiki.asterisk.org/wiki/display/AST/SIP+Realtime%2C+MySQL+table+structure). Con tan solo ejecutar ese comando en la consola de la base de datos estaremos listos para funcionar. No obstante y si nos paramos a pensar en toda la información que hay nos puede empezar a dar vueltas la cabeza... Gracias a la documentación de [asterisk docs](http://www.asteriskdocs.org/en/3rd_Edition/asterisk-book-html-chunk/I_section12_tt1465.html) nos dimos cuenta de que con mucha menos información podíamos seguir funcionando. Entre esta información y los errores que mostraba la **CLI** de `asterisk` llegamos a la siguiente descripción de una tabla que si bien es mucho más concisa nos permite trabajar sin problema alguno:

```sql
CREATE TABLE `sipconf` (
  `type` varchar(6) DEFAULT NULL,
  `name` varchar(128) DEFAULT NULL,
  `secret` varchar(128) DEFAULT NULL,
  `context` varchar(128) DEFAULT NULL,
  `host` varchar(128) DEFAULT NULL,
  `ipaddr` varchar(128) DEFAULT NULL,
  `port` varchar(5) DEFAULT NULL,
  `regseconds` bigint(20) DEFAULT NULL,
  `defaultuser` varchar(128) DEFAULT NULL,
  `fullcontact` varchar(128) DEFAULT NULL,
  `regserver` varchar(128) DEFAULT NULL,
  `useragent` varchar(128) DEFAULT NULL,
  `lastms` int(11) DEFAULT NULL,
  `callbackextension` varchar(40) DEFAULT NULL
);
```

Introducir un nuevo usuario se convierte por tanto en una sola query a esta tabla. El usuario que nosotros hemos usado de ejemplo es:

```sql
INSERT INTO `sipconf` (type, name, secret, context, host, defaultuser) VALUES ('friend','foodb','foodb','from-internal','dynamic','foodb');
```

Con lo anterior creamos un usuario idéntico a los que describíamos al principio del documento con nombre de usuario y contraseña `foodb/foodb`. El resto de columnas que no hemos rellenado serán establecidas por el propio `asterisk` cuando se registre este usuario. Recordemos que hemos establecido `host=dynamic`, esto es, el usuario se debe registrar... Si no tendríamos que rellenar más campos como la *IP* del terminal y demás.

Con la base de datos preparada debemos dirigirnos al archivo `extconfig.conf` para habilitar la posibilidad de cargar estos usuarios desde una base de datos externa. Debemos incluir las siguientes líneas:

```ini
[settings]
sippeers => odbc,asterisk,sipconf
sipusers => odbc,asterisk,sipconf
```

Con esto le decimos a `asterisk` que también busque usuarios a través del driver `odbc` en la base de datos `asterisk` y en la tabla `sipconf`. Fijémonos en que cargamos tanto usuarios como peers desde la misma tabla porque tenemos un campo `type` que nos permite distinguir el tipo sin problema.

Para que todo esto funcione como esperamos debemos habilitar la posibilidad de registrar usuarios de este modo en el archivo `sip.conf` para que se cargue su registro en memoria. De lo contrario solo podrían hacer llamadas... Podemos lograrlo con tan solo incluir:

```ini
rtcachefriends=yes
```

Con esto le decimos a `astrisk` que queremos que los usuarios que estén introducidos en la base de datos se incluyan en la memoria del programa solo cuando estos se registren. Por eso si ejecutamos `sip show peers` sin que se haya registrado nadie no observaremos ningún cambio hasta que el terminal en cuestión "inicie sesión". En otras palabras, se tratará igual a los usuarios del archivo de confiugración y a los que vienen de la base de datos una vez que estos últimos se hayan registrado.

Finalmente debemos recargarel manejador del canal desde la terminal de `asterisk` con `module reload chan_sip.so` y todo está listo para funcionar. Solo nos queda explicar cómo conseguir que `asterisk` sea capaz de comunicarse con esta base de datos externa.

### Comunicando a `asterisk` con el exterior: conectores **ODBC**
Dada la cantidad de bases de datos que existen debemos de alguna manera generar una interfaz que homogenice el acceso a cualquiera de ellas. Es por eso que aparecen los conectores **ODBC** que nos permiten insertarlos entre `asterisk` y el sistema gestor de bases de datos en cuestión para que pueda traducir las peticiones y repuestas para cada uno de los dos sistemas. Para ello debemos instalar la implementación de estos conectores para sistemas UNIX junto con sus dependencias. Lo podemos lograr con tan solo ejecutar:

```bash
sudo apt update && sudo apt -y install unixodbc libltdl7 libltdl-dev
```

Después tendremos que navegar hasta la página web de MySQL para descargar su propio conector ODBC desde [aquí](https://dev.mysql.com/downloads/connector/odbc/) para la versión correcta (la nuestra es la `18.04 Bionic Beaver`). Depués podemos seguir la guía de instalación de la [documentación](https://dev.mysql.com/doc/connector-odbc/en/connector-odbc-installation-binary-unix-tarball.html) que puede resumirse en las siguientes instrucciones ejecutadas desde un directorio que contenga el archivo descargado:

```bash
tar -xvf mysql_odbc_connector.tar.gz
cd mysql-connector-odbc-8.0.19-linux-ubuntu18.04-x86-64bit/
sudo cp bin/* /usr/local/bin/
sudo cp lib/* /usr/local/lib/
sudo myodbc-installer -a -d -n "MySQL_ODBC" -t "Driver=/usr/local/lib/libmyodbc8w.so"
```

Podemos comprobar que la instalación ha ido correctamente ejecutando la siguiente orden y comporbando que aparece el nombre que hemos pasado anteriormente `MySQL_ODBC`.

```bash
myodbc-installer -d -l
```

Debemos comentar que estos dirvers **ODBC** se distribuyen con versiones capaces de manejar solo caracteres `ASCII`, que son algo más rápidas y otras capaces de lidiar con caracteres **Unicode**. Dado que somos españoles y puede que alguien introduzca caracteres no ASCIII hemos preferido emplear esta segunda opción. Si se quiere la primera tan solo tendríamos que cambiar la cadena `"Driver=/usr/local/lib/libmyodbc8w.so"` por `"Driver=/usr/local/lib/libmyodbc8a.so"` en el proceso de instalación.

Ahora debemos indicarle a `unixodbc` dónde esta este nuevo driver que hemos configurado. Para ello debemos modificar el archivo `/etc/odbcinst.ini` e incluir lo siguiente:

```ini
[MySQL_ODBC]
Description = ODBC Connector for MySQL
Driver      = /usr/local/lib/libmyodbc8w.so
UsageCount  = 1
Pooling     = yes
```

Solo "apuntamos" `unixodbc` contra el driver que acabamos de instalar. Podemos comprobar que lo hemos instlado correctamente si ejecutamos:

```bash
odbcinst -q -d
```

Nos queda describir de alguna manera esta conexión para que `asterisk` pueda utilizarla. Todo ello se puede hacer a través del archivo `/etc/odbc.ini` en el que le indicamos a `asterisk` qué driver emplear para conectarse, dónde está el *socket* de conexión, su usuario, la base de datos que debe emplear... Al final debemos acabar con algo como:

```ini
[asterisk-mysql-cnx]
Driver       = MySQL_ODBC
Description  = MySQL connection for asterisk
server       = localhost
port         = 3306
Database     = asterisk
socket       = /var/run/mysqld/mysqld.sock
```

El usuario y contraseña que hemos configurado para el usuario de la base de datos los indicaremos en un archivo de configuración posterior. Además indicamos que estuvimos un buen rato hasta encontrar ese escurridizo *socket*... Esto que acabamos de configurar es lo que se denomina **DSN** (**D**ata **S**ource **N**ame), una descripción del conector que nos permite utilizarlo. En los siguientes pasos tendremos que referirnos a través del nombre `asterisk-mysql-cnx`.

Podemos probar si hemos configurado todo correctamente ejecutando la siguiente orden donde las opciones son el nombre del **DSN** y el usuario y contraseña con el que conectarnos a la base de datos, en nuestro caso, `asterisk/asterisk`:

```bash
sudo isql -v asterisk-connector asterisk asterisk
```

El siguiente paso consiste en indicarle a `asterisk` dónde está esta descripción del conector cosa que configuramos en el archivo `res_odbc.conf`:

```ini
[ENV]
[asterisk]
enabled => yes
dsn => asterisk-mysql-cnx
username => asterisk
password => asterisk
pre-connect => yes
```

Es aquí donde indicamos el nombre del **DSN** y el usuario y contraseña a emplear así como habilitamos esta conexión. Si ahora entramos en la **CLI** de `asterisk` y recargamos el módulo **ODBC** con `module reload res_odbc.so` y después ejecutamos `odbc show` deberíamos ver que la conexión `asterisk` con **DSN** `asterisk-mysql-cnx` aparece por pantalla.

Con esto ya tenemos a `asterisk` comunicado con el mundo exterior y la carga de usuarios desde la base de datos debería funcionar. También nos hemos animado a hacer peticiones a otras tablas de esta base de datos desde el plan de marcación.

### Haciendo queries a otras tablas
Para intentar llevar un control de las llamadas que se hacen a través de nuestra centralita decidimos crear la siguiente tabla:

```sql
CREATE TABLE `call_data` (
  `call_number` int(11) NOT NULL AUTO_INCREMENT,
  `caller_id` varchar(15) DEFAULT NULL,
  `called_exten` varchar(10) NOT NULL,
  PRIMARY KEY (`call_number`)
);
```

En la que tenemos un identificador de llamada que se incrementa automáticamente y recogemos el nombre del llamante y  llamado. Para poder interactuar con esta tabla tenemos que configurar una función con la sintaxis `SQL` correcta que lo haga por nosotros cosa que conseguimos en el archivo `func_odbc.conf`:

```ini
[general]
[SQL]           ; Define la función SQL en el plan de marcación
dsn=asterisk    ; Usa la conexión asterisk definida en res_odbc.conf
readsql=${ARG1} ; Ejecuta la query que se pasa como argumento
```

Está función que ya venía definida simplemente emplea la conexión `asterisk` definida en `res_odbc.conf` y acepta un parámetro desde el plan de marcación, la petición `SQL` completa que simplemente ejecuta. Podríamos definir un "envoltorio" para las funciones que queramos ofrecer al plan de marcación pero dado lo sencillas que son nuestras peticiones preferimos explicitarlas en el plan de marcación ya que creems que son fáciles de comprender y no dificultan el manejo del mismo.

En el plan de marcación encontraremos pues líneas como:

```ini
; Extensión 100
same => n,Verbose(${ODBC_SQL(INSERT INTO call_data (caller_id, called_exten) VALUES (\"${CALLERID(all):4:-1}\", ${GLOBAL(${EXTEN})})))

; Subrutinas store-data y store-data-end (${ARG1} == ${EXTEN}, el parámetro se pasa desde la extensión de llamadas)
exten => s,1,Verbose(${ODBC_SQL(INSERT INTO call_data (caller_id, called_exten) VALUES (\"${CALLERID(all):4:-1}\", ${GLOBAL(${ARG1})})))
```

En ellas simplemente llamamos a la función `ODBC_SQL()` (se añade el prefijo `ODBC` para garantizar que los nombres son únicos aunque podemos variarlo con la opción `prefix` en `func_odbc.conf`) y el parámetro que le pasamos es una query `SQL` normal y corriente donde empleamos variables del canal para obtener información significativa. Destacamos que como en las peticiones `SQL` las cadenas deben aparecer encerradas entre comillas (`""`) tenemos que escapar estos caracteres con `\`. No ocurre lo mismo con `${EXTEN}` ya que es un entero. Además de este detalle hemos querido "limpiar" el nombre del llamante ya que el valor crudo contenía `3` espacios antes del nombre y encerraba éste entre `<>`. Para ello cogemos solo los caracteres desde la posición `4` ignorando el último, de ahí el sufijo `:4:-1`.

Además de esta línea de acción también podemos emplear scripts que se comuniquen sirectamente con estas bases de datos saltándonos toda la infraestructura de **ODBC** en el proceso. Hemos aplicado esta solución con una base da datos *MongoDB* que es *noSQL*. Lo comentaremos más adelnate. Nos metemos ahora de lleno con las colas de agentes.

## Añadiendo colas de atención a usuarios
