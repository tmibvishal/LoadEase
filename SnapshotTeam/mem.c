#include <stdlib.h>
#include <unistd.h>
#include <stdio.h>

int main() {

    size_t mem_size = 1024 * 1024 * 256;
    mem_size *= 4;
    
    char *p = (char *) malloc(mem_size);

    int z = 0;

    for (int i = 0; i < 5; i++) {
        for (size_t k = 0; k < mem_size; k++) {
            size_t idx = k;
            p[idx] += 1;
            p[idx] *= p[idx];
            z += p[idx];
        }
    }
    printf("done..\n");
    fflush(stdout);
    sleep(1000);
    return z;
}