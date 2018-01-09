#include "opus.h"
#include <iostream>

int main()
{
  std::cout << opus_get_version_string() << std::endl;
  return 0;
}
