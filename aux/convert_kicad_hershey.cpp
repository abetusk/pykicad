#include <stdio.h>
#include <stdlib.h>

#include "newstroke_font.h"

int main(int argc, char **argv)
{
  int i, j, k;
  int n = 128-32;
  int ch0, ch1;
  const char *pch;
  int x, y;

  int base_x = 0, base_y = 0;
  int dx = 100, dy = 100;

  int xsta;
  int xsto;
  int y_off = 11;
  int first = 0, first_line = 0;
  int art_count;

  n = newstroke_font_bufsize;

  //printf("%i\n", newstroke_font_bufsize);
  //exit(0);

  printf("{\n");
  

  for (i=0; i<n; i++)
  {
    //printf("# '%s' %i %c\n", newstroke_font[i], i, (char)i);
    //

    printf("  \"%i\" : " , i + 32);
    printf("  {\n");

    printf("    \"scale_factor\" : \"%0.20f\",\n", 1.0/21.0 );

    pch = newstroke_font[i];

    int xsta = *pch++ - 'R';
    int xsto = *pch++ - 'R';

    printf("    \"xsta\" : \"%i\",\n", xsta );
    printf("    \"xsto\" : \"%i\",\n", xsto );
    printf("    \"art\" : [\n");

    first = 1;
    first_line = 1;
    art_count=0;


    //printf("# xsta: %i, xsto: %i\n", xsta, xsto);
    while (*pch)
    {

      ch0 = *pch++;
      if (ch0)
      {
        ch1 = *pch++;
      }
      else
      {
        continue;
      }


      x = ch0 - 'R';
      y = ch1 - 'R';

      if ((x == -50) && (y == 0))
      {
        //printf(" (pen up)\n");
        printf("],\n");
        //printf("      [ " );
        first_line=0;
        first = 1;
      }
      else 
      {
        if (first) 
        {
          printf("      [");
          art_count++;
        }

        printf(" %s{ \"x\": %i, \"y\": %i }", 
            first ? "" : "," ,
            x + base_x - xsta, 
            -(y - y_off) + base_y );
        first = 0;
      }

    }

    //base_x += dx;
    if (art_count>0) printf("]\n");
    printf("\n    ]\n");

    printf("  }%s\n", (i!=(n-1)) ? "," : "" );
    printf("\n");



  }

  printf("}\n");
}

