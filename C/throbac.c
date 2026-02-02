/*
C implementations of the Throbac string concatenation function
`__throbac_cat` (provided for you) and the two Throbac built-in
functions `stringlength` and `substring`

Author: OCdt Syed, OCdt Noyes

Version: 2026-01-29
*/

#include <stdlib.h>
#include <string.h>

#include "throbac.h"

char *__throbac_cat(char *first, char *second) {
    size_t length = strlen(first) + strlen(second) + 1;
    void *value = malloc(length);
    if (value == 0) {
        abort();
    }
    strcpy((char *) value, first);
    return strcat((char *) value, second);
}

int stringlength(char *str) {
    return (int)strlen(str);
}

char *substring(char* str, int start, int length) {
    if (start < 0 ||  start > length || length > strlen(str) - 1 || start + length > strlen(str)) abort();
    char *sub = malloc(length + 1);
    if (!sub) abort();

    strncpy(sub, str + start, length);
    sub[length] = '\0';

    return sub;
}
