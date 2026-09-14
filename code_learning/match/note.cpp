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


/*
**C++ 加速 cin/cout 的经典语句，必须放在 main 函数开头，所有 cin/cout 之前**。
1-关闭同步后，不能混用 cin/cout 和 scanf/printf!
输出顺序会乱，缓冲区独立。要么全用 C++ 流，要么全用 C IO。
2. 对 `endl` 影响：`endl` 强制刷新缓冲区，非常耗性能；
加速代码里**尽量用 `'\n'` 代替 `endl`
*/
ios::sync_with_stdio(false);
cin.tie(nullptr);

/*
**小根堆**
* - **① `long long`**：堆里存的元素类型（果子堆的重量）。
- **② `vector<long long>`**：底层容器，堆的数据存在这个 
vector 里（一般固定用它，不用改）。
- **③ `greater<long long>`**：比较规则，`greater` 表示 
"大的优先级低"，于是**堆顶 `pq.top()` 永远是最小值** —— 
这就是小根堆。
*/
//小根堆的使用
priority_queue<long long, vector<long long>, greater<long long>> pq;
for (int i = 0; i < n; ++i) {
	long long a;
	cin >> a;
	pq.push(a);
}

long long ans = 0;
while (pq.size() > 1) {
	// 取两个最小的
	long long x = pq.top(); pq.pop();
	long long y = pq.top(); pq.pop();
	ans += x + y;
	pq.push(x + y);
}

/*
双队列处理果子问题
*/
vector<long long> b;          // 新堆队列（自动有序）
int i = 0, j = 0;             // i: a 用到的位置；j: b 用到的位置（相当于 b 的队头指针）

auto takeMin = [&]() -> long long {
	if (i == n)             return b[j++];   // a 用完了，只能从 b 取
	if (j == (int)b.size()) return a[i++];   // b 用完了，只能从 a 取
	return a[i] < b[j] ? a[i++] : b[j++];    // 比较两个队头，取小的
	};

while ((n - i) + ((int)b.size() - j) > 1) {  // 剩下的堆数 > 1 就继续
	long long x = takeMin();   // 最小的堆
	long long y = takeMin();   // 第二小的堆
	long long s = x + y;
	ans += s;                  // 本次合并的代价
	b.push_back(s);            // 新堆放进 b 队尾（它 ≥ 上一个新堆，b 保持有序）
}
