public class reverseString {
    public static void main(String[] args){
        String str = "Automation";
        String reverse = new StringBuilder(str).reverse().toString();
        System.out.println(reverse);
    }
}
