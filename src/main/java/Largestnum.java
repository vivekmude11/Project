public class Largestnum {
    public void main(String[] args){
        int [] arr = {10, 20,30, 40};
        int largest = arr[0];
        for (int num : arr){
            if (num> largest){
                largest=num;

            }
        }
        System.out.println(largest);

    }
}
