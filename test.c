void f(int a) {}
int g(int b) {
	int x = 10;
	int y = 100;

	for (int i = 0; i < 10; i ++) {
		x *= i + 1;
	}

	return b + x + y;
}
