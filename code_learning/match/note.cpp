/*
**快速读取整数**
算法竞赛用,`cin` 默认较慢，数据量大时容易超时；
`scanf` 快一点；
`getchar()` 手写快读是最快的读整数方式。
*/

int read() {
	int x = 0, f = 1;
	char c = getchar();
	while (c < '0' || c>'9') {
		//跳过非数字字符（空格、回车）
		if (c == '-') f = -1;
		c = getchar();
	}
	//拼接数字
	while (c >= '0' && c <= '9') {
		x = x * 10 + c - '0';
		c = getchar();
	}
	return x * f;
}

/*
**c++sor函数的使用**
std::sort() 是 C++ 标准库中的一个函数，
用于对数组或容器中的元素进行排序。
它的默认排序方式是升序排列，
但也可以通过自定义比较函数来实现其他排序方式。
*/

//fuction_1
vector<int> v = { 3,2,1 };
sort(v.begin(), v.end()); // 升序排序
//fuction_2
bool cmp(int a, int b) {
	return a > b; // 降序排序
}
sort(v.begin(), v.end(), cmp); // 使用自定义比较函数进行排序
//v.begin() 和 v.end() 分别表示容器 v 的起始和结束迭代器，
//数组可以退化为指针，使用数组名和数组名加上元素个数即可。
