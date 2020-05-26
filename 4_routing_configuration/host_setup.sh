#!/bin/bash

# Actualizamos los repositorios e instalamos quagga
sudo apt update && sudo apt install quagga

# Notas curiosas
    # Nuestra shell, bash, permite utilizar una estructura de refirección conocida como `Here Documents`.
    # Podemos consultar la línea 1307 de su manual (man bash) para encontrar más información pero la
    # idea básica es que le damos a la shell una "marca" para que lea la entrada que le pasamos hasta que
    # lea dicha cadena. Todo lo que haya cogido hasta entonces lo pegará en stdin para que el proceso
    # que hemos invocado lo pueda leer. Esta marca puede ser lo que queramos. Por costumbre solemos elegir
    # palabras en mayúsculas. Frecuentemente encontramos las marcas 'EOF' y 'EOD'.
    #
    # Al pegar esta entrada en stdin es muy típico que se use con comandos como 'cat'. No
    # debemos olvidar que es la shell quien hace esta redirección, no el programa que estemos lanzando.
    # Por ello, lo siguiente generaría el archivo 'foo' cuyo contenido sería:

    # Hello
    # there
    # !

    # La orden en cuestión es:

    # cat > foo <<STOP
    # Hello
    # there
    # !
    # STOP

    # Comento esto porque buscando un ejemplo de aprovisionamiento con Vagrant he topado con un archivo que lo usaba y no sabía
    # si era algo propio de 'cat' o de la propia shell...