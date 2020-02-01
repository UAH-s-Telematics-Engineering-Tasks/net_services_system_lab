# Notes on compiling with debugging options
If you want a more vervosy output you can compile with the following command:

```
gcc -o prog_name.ex prog_name.c -DDBG
```

The `-DDBG` option `#defines` the constant `DBG` with a value of `1` when compiling and we use that as a switch to include some code parts. It's mainly just `printf()`s and a way to exit the program through a signal handler to avoid being hung up at the listening stage... If you happen to end up with a program that can't be terminated with `CTRL+C` (like us most of the time) you can run `ps -ax | grep prog_name` from another terminal to get the programs `PID` and then execute `kill prog_pid` to stop it withoug having to close the terminal every once in a while!