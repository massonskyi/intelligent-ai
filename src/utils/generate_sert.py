#!/usr/bin/env python3
"""
Скрипт для генерации самоподписанных SSL-сертификатов с использованием Python.
"""
import os
import subprocess
import sys
from pathlib import Path
print(f"Определена платформа: {sys.platform}")  # Должно быть "win32" для Windows

if sys.platform == "win32":
    # generate_ssl_certs_windows.py
    """
    Скрипт для генерации самоподписанных SSL-сертификатов на Windows.
    """
    import os
    import subprocess
    import sys
    from pathlib import Path


    def check_openssl_installed():
        """Проверяет, установлен ли OpenSSL на Windows."""
        try:
            result = subprocess.run(
                ["where", "openssl"],  # Используем Windows-специфичную команду
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                text=True
            )
            print(f"OpenSSL найден по пути: {result.stdout.strip()}")
            return True
        except subprocess.CalledProcessError:
            print("Системные пути поиска:")
            subprocess.run(["echo", "%PATH%"], shell=True)
            return False


    def openssl_install_instructions():
        """Выводит инструкции по установке OpenSSL на Windows."""
        print("\nOpenSSL не установлен или не добавлен в PATH на вашем компьютере.")
        print("\nВарианты установки OpenSSL на Windows:")
        print("1. Используйте Chocolatey (https://chocolatey.org/):")
        print("   choco install openssl")
        print("\n2. Скачайте установщик с официального сайта:")
        print("   https://slproweb.com/products/Win32OpenSSL.html")
        print("   (Рекомендуется скачать 'Win64 OpenSSL v1.1.1' или новее)")
        print("\n3. Для разработчиков можно использовать OpenSSL из Git for Windows:")
        print("   https://gitforwindows.org/")
        print("\nПосле установки убедитесь, что OpenSSL добавлен в системную переменную PATH и перезапустите скрипт.")


    def generate_certificates(key_path="key.pem", cert_path="cert.pem"):
        """
        Генерирует самоподписанные SSL-сертификаты на Windows.

        Args:
            key_path: Путь для сохранения приватного ключа
            cert_path: Путь для сохранения сертификата
        """
        print(f"Генерация SSL-сертификатов: {key_path} и {cert_path}")

        # Проверка наличия существующих файлов
        if Path(key_path).exists() or Path(cert_path).exists():
            response = input("Файлы уже существуют. Перезаписать? (y/n): ")
            if response.lower() != 'y':
                print("Операция отменена.")
                return False

        try:
            # Создание приватного ключа
            subprocess.run([
                "openssl", "genrsa",
                "-out", str(Path(key_path).absolute()),
                "2048"
            ], check=True, shell=True)

            # Создание запроса на сертификат (CSR)
            print("\nЗаполните следующую информацию для сертификата или нажмите Enter для значений по умолчанию:")

            # Информация о субъекте сертификата
            subject = {
                "C": input("Страна (2 буквы) [RU]: ") or "RU",
                "ST": input("Регион/Штат [Moscow]: ") or "Moscow",
                "L": input("Город [Moscow]: ") or "Moscow",
                "O": input("Организация [Development]: ") or "Development",
                "OU": input("Подразделение [IT]: ") or "IT",
                "CN": input("Общее имя (домен/IP) [localhost]: ") or "localhost"
            }

            subject_str = "/" + "/".join(f"{key}={value}" for key, value in subject.items())

            # Временный файл CSR
            csr_path = "csr.pem"

            subprocess.run([
                "openssl", "req",
                "-new",
                "-key", key_path,
                "-out", csr_path,
                "-subj", subject_str
            ], check=True, shell=True)

            # Создание самоподписанного сертификата
            validity_days = input("\nСрок действия сертификата в днях [365]: ") or "365"

            subprocess.run([
                "openssl", "x509",
                "-req",
                "-days", validity_days,
                "-in", csr_path,
                "-signkey", key_path,
                "-out", cert_path
            ], check=True, shell=True)

            # Удаление временного CSR
            os.remove(csr_path)

            print(f"\nSSL-сертификаты успешно сгенерированы:")
            print(f"- Приватный ключ: {key_path}")
            print(f"- Сертификат: {cert_path}")

            # Вывод информации о созданном сертификате
            print("\nИнформация о сертификате:")
            cert_info = subprocess.run([
                "openssl", "x509",
                "-in", cert_path,
                "-text",
                "-noout"
            ], check=True, stdout=subprocess.PIPE, text=True, shell=True).stdout

            # Вывод основной информации о сертификате
            for line in cert_info.split('\n'):
                if any(info in line for info in ['Subject:', 'Issuer:', 'Not Before:', 'Not After :']):
                    print(line.strip())

            return True

        except subprocess.SubprocessError as e:
            print(f"Ошибка при генерации сертификатов: {e}")
            return False


    def main():
        """Основная функция скрипта."""
        print("Генерация SSL-сертификатов для локальной разработки на Windows\n")

        if not check_openssl_installed():
            print("OpenSSL не установлен или недоступен в системе Windows.")
            openssl_install_instructions()
            input("\nНажмите Enter для выхода...")
            sys.exit(1)

        # Пути для сертификатов можно изменить здесь
        key_path = "key.pem"
        cert_path = "cert.pem"

        success = generate_certificates(key_path, cert_path)

        if success:
            print("\nПримечание: Это самоподписанный сертификат, подходящий только для разработки.")
            print("Для производственной среды рекомендуется получить сертификат от доверенного центра сертификации.")
        else:
            print("\nНе удалось сгенерировать сертификаты.")
            sys.exit(1)

        input("\nНажмите Enter для выхода...")


    if __name__ == "__main__":
        print("Проверка окружения:")
        subprocess.run(["where", "openssl"], shell=True)
        subprocess.run(["openssl", "version"], shell=True)
        main()
else:
    def check_openssl_installed():
        """Проверяет, установлен ли OpenSSL."""
        try:
            subprocess.run(["openssl", "version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False


    def generate_certificates(key_path="key.pem", cert_path="cert.pem"):
        """
        Генерирует самоподписанные SSL-сертификаты.

        Args:
            key_path: Путь для сохранения приватного ключа
            cert_path: Путь для сохранения сертификата
        """
        print(f"Генерация SSL-сертификатов: {key_path} и {cert_path}")

        # Проверка наличия существующих файлов
        if Path(key_path).exists() or Path(cert_path).exists():
            response = input("Файлы уже существуют. Перезаписать? (y/n): ")
            if response.lower() != 'y':
                print("Операция отменена.")
                return False

        try:
            # Создание приватного ключа
            subprocess.run([
                "openssl", "genrsa",
                "-out", key_path,
                "2048"
            ], check=True)

            # Создание запроса на сертификат (CSR)
            print("\nЗаполните следующую информацию для сертификата или нажмите Enter для значений по умолчанию:")

            # Информация о субъекте сертификата
            subject = {
                "C": input("Страна (2 буквы) [RU]: ") or "RU",
                "ST": input("Регион/Штат [Moscow]: ") or "Moscow",
                "L": input("Город [Moscow]: ") or "Moscow",
                "O": input("Организация [Development]: ") or "Development",
                "OU": input("Подразделение [IT]: ") or "IT",
                "CN": input("Общее имя (домен/IP) [localhost]: ") or "localhost"
            }

            subject_str = "/" + "/".join(f"{key}={value}" for key, value in subject.items())

            # Временный файл CSR
            csr_path = "csr.pem"

            subprocess.run([
                "openssl", "req",
                "-new",
                "-key", key_path,
                "-out", csr_path,
                "-subj", subject_str
            ], check=True)

            # Создание самоподписанного сертификата
            validity_days = input("\nСрок действия сертификата в днях [365]: ") or "365"

            subprocess.run([
                "openssl", "x509",
                "-req",
                "-days", validity_days,
                "-in", csr_path,
                "-signkey", key_path,
                "-out", cert_path
            ], check=True)

            # Удаление временного CSR
            os.remove(csr_path)

            print(f"\nSSL-сертификаты успешно сгенерированы:")
            print(f"- Приватный ключ: {key_path}")
            print(f"- Сертификат: {cert_path}")

            # Вывод информации о созданном сертификате
            print("\nИнформация о сертификате:")
            cert_info = subprocess.run([
                "openssl", "x509",
                "-in", cert_path,
                "-text",
                "-noout"
            ], check=True, stdout=subprocess.PIPE, text=True).stdout

            # Вывод основной информации о сертификате
            for line in cert_info.split('\n'):
                if any(info in line for info in ['Subject:', 'Issuer:', 'Not Before:', 'Not After :']):
                    print(line.strip())

            return True

        except subprocess.SubprocessError as e:
            print(f"Ошибка при генерации сертификатов: {e}")
            return False


    def main():
        """Основная функция скрипта."""
        print("Генерация SSL-сертификатов для локальной разработки\n")

        if not check_openssl_installed():
            print("OpenSSL не установлен или недоступен. Установите OpenSSL перед запуском скрипта.")
            sys.exit(1)

        # Пути для сертификатов можно изменить здесь
        key_path = "key.pem"
        cert_path = "cert.pem"

        success = generate_certificates(key_path, cert_path)

        if success:
            print("\nПримечание: Это самоподписанный сертификат, подходящий только для разработки.")
            print("Для производственной среды рекомендуется получить сертификат от доверенного центра сертификации.")
        else:
            print("\nНе удалось сгенерировать сертификаты.")
            sys.exit(1)


    if __name__ == "__main__":
        main()