#include <stdio.h>

int ones_complement_16_bit_sum(int, char);
void print_binary_16_bit_n(int);

int main(void) {
    int result;
    printf("Result: ");
    print_binary_16_bit_n(result = ones_complement_16_bit_sum(0x0A << 16 | ~0xC & 0xFFFF, 1));
    printf("Non-inverted result: %u\n", result & 0xFFFF);
    printf("Inverted result: %u\n", ~result & 0xFFFF);
    return 0;
}
/*
    The function will add 2 16-bit numbers according to the 1's Complement logic
    It returns the result in the 16 Least Significant Bits of the returned value
    The caller must take that into account and mask the retruned value accordingly
*/
int ones_complement_16_bit_sum(int x, char recirculate) {
    // n = 16 as that's the boundry between the numbers. We prefer to show the logic to obtain that result
    int aux_result = 0, carry = 0, y = x, n = sizeof(x) * (8 / 2);
    // If we are just recirculating the carry take into account the offset we apply to the second operand so that
    // we don't have to rewrite the condition within the for loop...
    if (!recirculate)
        y = 1 << n;

    for (int k = 0; k < n; k++) {
            if (((x & 0x1 << k) >> k) != ((y & 0x1 << k + n) >> k + n))
                aux_result |= (carry ^ 0x1) << k;
            else {
                aux_result |= carry << k;
                if (x & 0x1 << k)
                    carry = 1;
                else
                    carry = 0;
            }
        }
    if (carry && recirculate)
        aux_result = ones_complement_16_bit_sum(aux_result, 0);

    return aux_result & 0xFFFF;
}

void print_binary_16_bit_n(int n) {
    for (int i = 15; i >= 0; i--) {
        if (n & 1 << i)
            printf("1");
        else
            printf("0");
    }
    printf("\n");
}