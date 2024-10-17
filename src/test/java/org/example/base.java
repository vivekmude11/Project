package org.example;

import io.github.bonigarcia.wdm.WebDriverManager;
import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;

import java.time.Duration;

public class base {
    public static void main(String[] args) throws InterruptedException {
        WebDriverManager.chromedriver().setup();
        WebDriver driver = new ChromeDriver();
        driver.get("https://qa-app.zaggleems.com/");
        driver.manage().window().maximize();
        driver.manage().timeouts().implicitlyWait(Duration.ofSeconds(5));
        driver.findElement(By.xpath("//input[@id='normal_login_username']")).sendKeys("titan3@yopmail.com");
        WebElement passwordField = driver.findElement(By.xpath("//input[@id='normal_login_password']"));
        passwordField.sendKeys("Zaggle@123");
        WebElement loginButton = driver.findElement(By.xpath("//button[@class='ant-btn red-btn ant-btn-primary']"));
        loginButton.click();
        Thread.sleep(5000);
        driver.quit();
    }
}