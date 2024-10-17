package org.example;

import io.github.bonigarcia.wdm.WebDriverManager;
import org.openqa.selenium.By;
import org.openqa.selenium.JavascriptExecutor;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;

import java.nio.file.Paths;
import java.time.Duration;
//import java.time.Duration;

public class Expenses {
    public static void main(String[] args) {
        WebDriverManager.chromedriver().setup();
        ChromeOptions options = new ChromeOptions();
        options.setAcceptInsecureCerts(true);  // Allows handling insecure SSL certificates
        WebDriver driver = new ChromeDriver(options);

        try {
            driver.get("https://qa-app.zaggleems.com/");
            driver.manage().window().maximize();
            driver.manage().timeouts().implicitlyWait(Duration.ofSeconds(5));
            driver.findElement(By.xpath("//input[@id='normal_login_username']")).sendKeys("titan3@yopmail.com");
            WebElement passwordField = driver.findElement(By.xpath("//input[@id='normal_login_password']"));
            passwordField.sendKeys("Zaggle@123");
            WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(20));
            WebElement loginButton = wait.until(ExpectedConditions.visibilityOfElementLocated(By.xpath("//button[@class='ant-btn red-btn ant-btn-primary']")));
            wait.until(ExpectedConditions.elementToBeClickable(loginButton)).click();WebElement expense = wait.until(ExpectedConditions.elementToBeClickable(By.xpath("//a[@class='ellipsis' and @href='/user-expenses']")));
            expense.click();
            WebElement addExpense = wait.until(ExpectedConditions.elementToBeClickable(By.xpath("//button[@type='button' and .//span[text()='Add Expense']]")));
            addExpense.click();
            WebElement Addexpense = driver.findElement(By.xpath("//li[normalize-space()='Add Expense']"));
            Addexpense.click();
            WebDriverWait wait1 = new WebDriverWait(driver, Duration.ofSeconds(40));
            WebElement dateInput = wait.until(ExpectedConditions.elementToBeClickable(By.xpath("//input[@placeholder='Select date']")));
            ((JavascriptExecutor) driver).executeScript("arguments[0].click();", dateInput);
            WebElement dateToSelect = wait.until(ExpectedConditions.elementToBeClickable(By.xpath("//div[normalize-space()='15']")));
            dateToSelect.click();
            WebElement category = wait.until(ExpectedConditions.elementToBeClickable(By.xpath("//div[normalize-space()='Select Category']")));
            category.click();
            driver.findElement(By.xpath("//li[@role='option' and contains(@class, 'ant-select-dropdown-menu-item') and not(contains(@class, 'ant-select-dropdown-menu-item-disabled'))]/span[text()='1']")).click();
            wait.until(ExpectedConditions.invisibilityOfElementLocated(By.className("ant-spin ant-spin-spinning")));
            WebElement elementToClick = wait.until(ExpectedConditions.elementToBeClickable(By.xpath("//div[@class='ant-select-selection__placeholder']")));
            elementToClick.click();
            WebElement fileInput = wait.until(ExpectedConditions.elementToBeClickable(By.xpath("//p[@class='ant-upload-hint']")));
            fileInput.click();
            // Specify the file path you want to upload (make sure the path is correct)
            String filePath = Paths.get("/Users/zaggle/Downloads/Image (9).png.txt").toAbsolutePath().toString(); // Update the file path
            fileInput.sendKeys(filePath);
            WebElement uploadButton = wait.until(ExpectedConditions.elementToBeClickable(By.xpath("//button[@id='open-button']"))); // Replace with actual button XPath
            uploadButton.click();

            Thread.sleep(5000);

        } catch (Exception e) {
            e.printStackTrace();  // Print error stack trace for debugging
        } finally {
            // Ensure WebDriver quits properly
            if (driver != null) {
                driver.quit();
            }
        }
    }
}
