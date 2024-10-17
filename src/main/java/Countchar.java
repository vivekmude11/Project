import java.util.HashMap;

public class Countchar {
    public static void main(String[] args) {
        String str = "Automation";
        HashMap<Character, Integer> charCount = new HashMap<>();

        // Loop through each character in the string
        for (char ch : str.toCharArray()) {
            // Use getOrDefault to handle the case where the character is not yet in the map
            charCount.put(ch, charCount.getOrDefault(ch, 0) + 1);
        }

        // Print the character frequencies
        System.out.println(charCount);
    }
}