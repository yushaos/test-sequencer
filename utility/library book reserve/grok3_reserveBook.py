import tkinter as tk
from tkinter import messagebox
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import schedule
import time
import threading
import queue
import datetime

# Global variables
running = True
status_queue = queue.Queue()

def reserve_book(book_link):
    """Function to reserve the book using Selenium."""
    driver = webdriver.Chrome()
    try:
        driver.get(book_link)
        status_queue.put("Navigating to book page: " + book_link)
        try:
            # First try to find and click the login button
            login_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[@aria-label='Log into your hoopla account']"))
            )
            login_button.click()
            status_queue.put("Login button clicked successfully.")
            
            # Now handle the login form using aria-labels with explicit waits
            username_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@aria-label='Email']"))
            )
            time.sleep(1)
            
            username_field.clear()
            username_field.send_keys("yushaoss@gmail.com")
            
            password_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@aria-label='Password']"))
            )
            password_field.clear()
            password_field.send_keys("x24EfT6a")
            
            # Click the login button
            login_submit = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
            )
            login_submit.click()
            status_queue.put("Login submitted with provided credentials.")
            
            time.sleep(3)
            
            # After login, navigate back to book page
            driver.get(book_link)
            time.sleep(2)
            
            # Click the initial borrow button
            borrow_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "borrow-button"))
            )
            borrow_button.click()
            status_queue.put("Initial borrow button clicked.")
            
            # Wait for and click the "Borrow Title" button in the popup
            borrow_title_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Borrow Title')]"))
            )
            borrow_title_button.click()
            status_queue.put("Borrow Title confirmation clicked.")
            
            # Check for error message
            try:
                error_message = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//p[contains(@class, 'text-red-700')]"))
                )
                if "daily borrow limit" in error_message.text:
                    status_queue.put("BORROW FAILED: Daily borrow limit reached. Will reset at midnight.")
                    return
            except:
                status_queue.put("Book borrowed successfully!")
            
            # Keep the browser window open
            while True:
                time.sleep(1)
                if not running:
                    break
                
        except Exception as e:
            status_queue.put(f"Error during login/borrow process: {str(e)}")
            return
            
    except Exception as e:
        status_queue.put(f"Error occurred: {str(e)}")
    finally:
        if driver:
            driver.quit()
            status_queue.put("Browser closed.")

def job():
    """Scheduled job to reserve the book."""
    book_link = book_link_entry.get()
    if not book_link:
        status_queue.put("Error: No book link provided.")
        return
    reserve_book(book_link)
    status_queue.put("Reservation completed at " + datetime.datetime.now().strftime("%H:%M:%S"))

def test_now():
    """Run the reservation immediately when Test Now button is clicked."""
    book_link = book_link_entry.get()
    if not book_link:
        status_queue.put("Error: No book link provided.")
        return
    reserve_book(book_link)
    status_queue.put("Test reservation completed at " + datetime.datetime.now().strftime("%H:%M:%S"))

def scheduling_loop(time_str):
    """Thread function to schedule the reservation daily."""
    schedule.every().day.at(time_str).do(job)
    status_queue.put(f"Scheduled to reserve book daily at {time_str}.")
    while running:
        schedule.run_pending()
        time.sleep(60)

def start_scheduling():
    """Start the scheduling process when the button is clicked."""
    book_link = book_link_entry.get()
    time_str = time_entry.get() or "00:00"
    try:
        datetime.datetime.strptime(time_str, "%H:%M")
    except ValueError:
        messagebox.showerror("Invalid Time", "Please enter a valid time in HH:MM format (e.g., 23:59).")
        return
    thread = threading.Thread(target=scheduling_loop, args=(time_str,), daemon=True)
    thread.start()
    status_queue.put(f"Scheduling started for {time_str} daily.")

def update_status():
    """Update the status box with messages from the queue."""
    try:
        while True:
            message = status_queue.get_nowait()
            status_text.insert(tk.END, message + "\n")
            status_text.see(tk.END)
    except queue.Empty:
        pass
    root.after(1000, update_status)

# GUI Setup
root = tk.Tk()
root.title("Book Reservation Scheduler")

tk.Label(root, text="Book Link:").grid(row=0, column=0, padx=5, pady=5)
book_link_entry = tk.Entry(root, width=50)
book_link_entry.grid(row=0, column=1, padx=5, pady=5)
book_link_entry.insert(0, "https://www.hoopladigital.com/title/16991265?utm_marquee=yes&utm_content=homepage_Marquee1")

tk.Label(root, text="Time (HH:MM):").grid(row=1, column=0, padx=5, pady=5)
time_entry = tk.Entry(root, width=10)
time_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)
time_entry.insert(0, "00:00")

# Start Scheduling Button
start_button = tk.Button(root, text="Start Scheduling", command=start_scheduling)
start_button.grid(row=2, column=0, padx=5, pady=10)

# Test Now Button
test_button = tk.Button(root, text="Test Now", command=test_now)
test_button.grid(row=2, column=1, padx=5, pady=10)

status_text = tk.Text(root, height=10, width=60)
status_text.grid(row=3, column=0, columnspan=2, padx=5, pady=5)

root.after(1000, update_status)

def on_closing():
    global running
    running = False
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()