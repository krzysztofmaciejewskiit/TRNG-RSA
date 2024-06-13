import os
import time
import asyncio
import hmac_drbg as prng
import round_trip_time as rtt
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from sympy import isprime, nextprime
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateNumbers, RSAPublicNumbers


# Funkcja do znajdowania dwóch różnych liczb pierwszych z listy losowych liczb
def find_two_distinct_primes_from_list(random_numbers):
    primes = []
    for num in random_numbers:
        if isprime(num) and num not in primes:
            primes.append(num)
        if len(primes) == 2:
            break
    while len(primes) < 2:
        next_prime = nextprime(random_numbers[-1])
        if next_prime not in primes:
            primes.append(next_prime)
        random_numbers.append(next_prime)
    return primes[0], primes[1]


# Funkcja do generowania kluczy RSA z użyciem podanych liczb pierwszych
def generate_custom_rsa_keys(p, q, e=65537):
    n = p * q
    phi = (p - 1) * (q - 1)

    # Obliczamy d, multiplikatywną odwrotność e modulo phi
    d = pow(e, -1, phi)

    # Generujemy klucze RSA z użyciem liczb pierwszych
    public_numbers = RSAPublicNumbers(e, n)
    private_numbers = RSAPrivateNumbers(
        public_numbers=public_numbers,
        d=d,
        p=p,
        q=q,
        dmp1=d % (p - 1),
        dmq1=d % (q - 1),
        iqmp=pow(q, -1, p)
    )

    private_key = private_numbers.private_key()
    public_key = private_key.public_key()

    return private_key, public_key

def sign_message(private_key, message):
    signature = private_key.sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return signature

def verify_signature(public_key, message, signature):
    try:
        public_key.verify(
            signature,
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except Exception as e:
        # print(f"Weryfikacja nie powiodła się: {e}")
        return False

def display_keys(private_key, public_key):
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')

    public_key_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')

    print(f"Klucz prywatny:\n{private_key_pem}\n")
    print(f"Klucz publiczny:\n{public_key_pem}\n")

def read_random_url(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    return prng.secrets.choice(lines).strip()

def extract_entropy(folder):
    entropy_bits = b''
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        if os.path.isfile(file_path):
            with open(file_path, 'rb') as file:
                entropy_bits += file.read()
    return entropy_bits

def trim_bits(value, num_bits):
    # Maskuje wartość, aby zachować tylko najbardziej znaczące 'num_bits' bitów.
    return value & ((1 << num_bits) - 1)

def clear_folder(folder):
    # Czyści wszystkie pliki z określonego folderu, tworząc go, jeśli nie istnieje.
    if not os.path.exists(folder):
        os.makedirs(folder)
    else:
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            if os.path.isfile(file_path):
                os.unlink(file_path)

async def create_rtt_threads(num_urls, url_data, rtt_folder, num_measurements):
    # Tworzy i uruchamia wątki do pomiarów RTT.
    tasks = []
    for i in range(num_urls):
        url = 'https://' + read_random_url(url_data)
        rtt_file = os.path.join(rtt_folder, f'{i + 1}.txt')
        task = asyncio.create_task(rtt.measure_rtt(url, rtt_file, num_measurements))
        tasks.append(task)
    await asyncio.gather(*tasks)

async def generate_random_number(num_urls, num_measurements, random_bytes, bit_length, rtt_folder, url_data):
    # Generuje losowy numer.
    await create_rtt_threads(num_urls, url_data, rtt_folder, num_measurements)

    entropy_bits = extract_entropy(rtt_folder)
    seed = prng.secrets.randbits(256).to_bytes(32, byteorder='big')
    drbg = prng.DRBG(seed)
    prng_value = drbg.generate(random_bytes)

    prng_value = trim_bits(int.from_bytes(prng_value, 'big'), bit_length)
    entropy_bits = trim_bits(int.from_bytes(entropy_bits, 'big'), bit_length)
    random_number = prng_value ^ entropy_bits

    return random_number

async def generate_random_numbers(num_iterations, num_urls, num_measurements, random_bytes, bit_length, rtt_folder, url_data):
    random_numbers = []
    for _ in range(num_iterations):
        random_number = await generate_random_number(num_urls, num_measurements, random_bytes, bit_length, rtt_folder, url_data)
        random_numbers.append(random_number)
    return random_numbers

async def main():
    num_iterations = 10  # Liczba losowych liczb do wygenerowania
    num_urls = 1
    num_measurements = 2
    random_bytes = 17
    bit_length = 136
    rtt_folder = 'RTTS'
    url_data = 'top_websites2.txt'

    start_time = time.time()
    random_numbers = await generate_random_numbers(num_iterations, num_urls, num_measurements, random_bytes, bit_length, rtt_folder, url_data)
    elapsed_time = time.time() - start_time

    print("Generated random numbers:")
    for i, number in enumerate(random_numbers, start=1):
        print(f"Iteration {i}: {number}")

    print(f"Total elapsed time: {elapsed_time:.2f} seconds")

    # Zapisz wyniki do pliku
    with open('random_numbers.txt', 'w') as file:
        for number in random_numbers:
            file.write(f'{number}\n')

    # Demonstracja podpisu cyfrowego
    message = b"Testowa wiadomosc do podpisu cyfrowego"
    print("Oryginalna wiadomość:", message.decode())

    # Znajdowanie dwóch różnych liczb pierwszych z listy losowych liczb
    p, q = find_two_distinct_primes_from_list(random_numbers)

    # Generowanie kluczy RSA
    private_key, public_key = generate_custom_rsa_keys(p, q)
    print("\n--- Oryginalna para kluczy ---")
    display_keys(private_key, public_key)

    # Podpisywanie oryginalnej wiadomości
    signature = sign_message(private_key, message)
    print("Podpis oryginalnej wiadomości:", signature.hex())

    # Weryfikacja podpisu oryginalnej wiadomości
    verification_result = verify_signature(public_key, message, signature)
    print("Weryfikacja oryginalnej wiadomości:", verification_result)

    # Zmiana treści wiadomości
    altered_message = b"Zmieniona wiadomosc do podpisu cyfrowego"
    print("\nZmieniona wiadomość:", altered_message.decode())

    # Próba weryfikacji oryginalnego podpisu ze zmienioną wiadomością (powinna się nie powieść)
    altered_verification_with_original_signature = verify_signature(public_key, altered_message, signature)
    print("Weryfikacja zmienionej wiadomości z oryginalnym podpisem:", altered_verification_with_original_signature)

    # Podpisywanie zmienionej wiadomości
    altered_signature = sign_message(private_key, altered_message)
    print("Podpis zmienionej wiadomości:", altered_signature.hex())

    # Weryfikacja podpisu zmienionej wiadomości (powinna się powieść)
    altered_verification_result = verify_signature(public_key, altered_message, altered_signature)
    print("Weryfikacja zmienionej wiadomości z nowym podpisem:", altered_verification_result)

    # Generowanie nowej pary liczb pierwszych z nowych losowych liczb
    new_random_numbers = await generate_random_numbers(num_iterations, num_urls, num_measurements, random_bytes, bit_length, rtt_folder, url_data)
    new_p, new_q = find_two_distinct_primes_from_list(new_random_numbers)

    # Generowanie nowej pary kluczy i weryfikacja
    new_private_key, new_public_key = generate_custom_rsa_keys(new_p, new_q)
    print("\n--- Nowa para kluczy ---")
    display_keys(new_private_key, new_public_key)
    new_verification_result_original = verify_signature(new_public_key, message, signature)
    new_verification_result_altered = verify_signature(new_public_key, altered_message, altered_signature)
    print("\nWeryfikacja oryginalnej wiadomości z nową parą kluczy:", new_verification_result_original)
    print("Weryfikacja zmienionej wiadomości z nową parą kluczy:", new_verification_result_altered)


if __name__ == "__main__":
    asyncio.run(main())
