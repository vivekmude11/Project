public class palindrome {
    public static void main(String[] args){
        String Str = "madam";
        String reverse=new StringBuilder(Str).reverse().toString();
        if (Str.equals(reverse)){
            System.out.println("String is palindrome");}
            else{
                System.out.println("String is not polindrome");
            }
        }

    }

