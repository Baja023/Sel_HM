import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By


def initialize_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Запуск в фоновом режиме
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    try:
        driver = webdriver.Chrome(options=chrome_options)
    except Exception as e:
        print("Ошибка при инициализации WebDriver:", e)
        sys.exit(1)
    return driver


def search_wikipedia(driver, query):
    driver.get("https://ru.wikipedia.org")
    try:
        search_box = driver.find_element(By.NAME, "search")
        search_box.send_keys(query)
        search_box.submit()
        time.sleep(2)  # Ожидание загрузки страницы
        # Проверка, не является ли страница страницей поиска
        if "Википедия:Поиск" in driver.title:
            print("Страница не найдена. Попробуйте другой запрос.")
            return None
        return driver.page_source
    except NoSuchElementException:
        print("Поле поиска не найдено.")
        return None


def get_page_title(driver):
    return driver.title.replace(" — Википедия", "")


def get_paragraphs(driver):
    try:
        content = driver.find_element(By.ID, "mw-content-text")
        paragraphs = content.find_elements(By.TAG_NAME, "p")
        para_texts = [para.text for para in paragraphs if para.text.strip() != ""]
        return para_texts
    except NoSuchElementException:
        print("Не удалось получить содержимое страницы.")
        return []


def get_links(driver):
    try:
        content = driver.find_element(By.ID, "mw-content-text")
        link_elements = content.find_elements(By.CSS_SELECTOR, "a[href^='/wiki/']")
        links = set()
        for link in link_elements:
            href = link.get_attribute('href')
            title = link.get_attribute('title')
            if title and not href.startswith("https://ru.wikipedia.org/wiki/Служебная:"):
                links.add(title)
            if len(links) >= 50:  # Ограничение для производительности
                break
        return sorted(links)
    except NoSuchElementException:
        print("Не удалось получить ссылки со страницы.")
        return []


def navigate_to_link(driver, link_title):
    try:
        # Используем ссылку по тексту
        link = driver.find_element(By.LINK_TEXT, link_title)
        link.click()
        time.sleep(2)  # Ожидание загрузки новой страницы
        return True
    except NoSuchElementException:
        print(f"Ссылка '{link_title}' не найдена на странице.")
        return False


def main():
    driver = initialize_driver()
    current_page_title = None

    try:
        query = input("Введите поисковый запрос: ").strip()
        if not query:
            print("Пустой запрос. Выход из программы.")
            return

        page_content = search_wikipedia(driver, query)
        if not page_content:
            return

        current_page_title = get_page_title(driver)
        print(f"\nТекущая страница: {current_page_title}")

        while True:
            print("\nЧто вы хотите сделать?")
            print("1. Листать параграфы текущей статьи")
            print("2. Перейти на одну из связанных страниц")
            print("3. Выйти из программы")
            choice = input("Введите номер действия: ").strip()

            if choice == '1':
                paragraphs = get_paragraphs(driver)
                if not paragraphs:
                    print("Нет доступных параграфов для отображения.")
                    continue
                for idx, para in enumerate(paragraphs, 1):
                    print(f"\nПараграф {idx}:\n{para}\n")
                    user_input = input(
                        "Нажмите Enter для следующего параграфа или введите 'q' для выхода: ").strip().lower()
                    if user_input == 'q':
                        break

            elif choice == '2':
                links = get_links(driver)
                if not links:
                    print("Связанных страниц не найдено.")
                    continue
                print("\nСвязанные страницы:")
                for idx, link in enumerate(links[:10], 1):  # Показываем первые 10 ссылок
                    print(f"{idx}. {link}")
                while True:
                    selection = input("Введите номер страницы для перехода или 'b' для возврата: ").strip().lower()
                    if selection == 'b':
                        break
                    if selection.isdigit():
                        num = int(selection)
                        if 1 <= num <= min(10, len(links)):
                            selected_link = links[num - 1]
                            success = navigate_to_link(driver, selected_link)
                            if success:
                                current_page_title = get_page_title(driver)
                                print(f"\nПерешли на страницу: {current_page_title}")
                            break
                        else:
                            print("Неверный номер. Пожалуйста, попробуйте снова.")
                    else:
                        print("Неверный ввод. Пожалуйста, попробуйте снова.")

            elif choice == '3':
                print("Выход из программы.")
                break

            else:
                print("Неверный выбор. Пожалуйста, попробуйте снова.")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
