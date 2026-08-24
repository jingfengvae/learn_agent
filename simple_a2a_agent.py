from a2a_server import A2AServer

def create_calculator_agent():
    """创建一个计算器智能体"""
    print ("创建一个计算器智能体...")

    calculator = A2AServer(
                name = "calculator-agent",
                description = "专业的数学计算器智能体",
                version = "1.0.0",
                capabilities = {
                    "math": ["addition", "subtraction", "multiplication", "division"],
                    "advanced": ["power", "sqrt", "factorial"]
                }
            )

    # 添加基础计算技能
    @calculator.skill("add")
    def add_numbers(query: str):
        """加法计算"""
        try:
            parts = query.strip().replace("计算", "").replace("加", "+").replace("加上", "+")

            if '+' in parts:
                numbers = [float(x.strip()) for x in parts.split('+')]
                result = sum(numbers)
                return f"计算结果: {' + '.join(map(str, numbers))} = {result}"
            else:
                return "请使用格式： 计算 5 + 3"
        except Exception as e:
            print (f"计算 {query} Error: {e}")
            return f"计算Error: {e}"

    @calculator.skill("sub")
    def subtraction_numbers(query: str):
        """减法计算"""
        try:
            parts = query.strip().replace("计算", "").replace("减", "-").replace("减去", "-")
    
            if '-' in parts:
                numbers = [float(x.strip()) for x in parts.split('-')]
                if len(numbers) == 2:
                    result = numbers[0] - numbers[1]
                    return f"计算结果: {' - '.join(map(str, numbers))} = {result}"
            return "请使用格式： 计算 5 - 3"
        except Exception as e:
            print (f"计算 {query} Error: {e}")
            return f"计算Error: {e}"
        
    @calculator.skill("multiply")
    def multiply_numbers(query: str):
        """乘法计算"""
        try:
            parts = query.strip().replace("计算", "").replace("乘以", "*").replace("x", "*")
    
            if '*' in parts:
                numbers = [float(x.strip()) for x in parts.split('*')]
                result = 1
                for num in numbers:
                    result *= num
                return f"计算结果: {' * '.join(map(str, numbers))} = {result}"
            else:
                return "请使用格式： 计算 5 * 3"
        except Exception as e:
            print (f"计算 {query} Error: {e}")
            return f"计算Error: {e}"

    @calculator.skill("division")
    def division_numbers(query: str):
        """除法计算"""
        try:
            parts = query.strip().replace("计算", "").replace("除以", "/")
        
            if '/' in parts:
                numbers = [float(x.strip()) for x in parts.split('*')]
                result = 1
                if len(numbers) == 2:
                    result = numbers[0] / numbers[1]
                return f"计算结果: {' / '.join(map(str, numbers))} = {result}"

            return "请使用格式： 计算 5 / 3"
        except Exception as e:
            print (f"计算 {query} Error: {e}")
            return f"计算Error: {e}"

    @calculator.skill("info")
    def get_info(query: str):
        """获取智能体信息"""
        return f"我是{calculator.name}, 可以进行基础数学计算。支持的功能: {list(calculator.skills.keys())}"
    
    return calculator
    

# 创建一个智能体    
calc_agent = create_calculator_agent()
if calc_agent:
    # 测试技能
    print ("\n 测试智能体技能：")
    test_queries = [
        "获取信息",
        "计算 4 * 10",
        "计算 1 + 5",
        "计算 6 - 3",
        "计算 6 除以 2"
    ]
    
    for query in test_queries:
        if "信息" in query:
            result = calc_agent.skills["info"](query)
        elif "+" in query:
            result = calc_agent.skills["add"](query)
        elif "*" in query or "×" in query or "乘以" in query:
            result = calc_agent.skills["multiply"](query)
        elif "-" in query:
            result = calc_agent.skills["sub"](query)
        elif "/" in query or "除以" in query:
            result = calc_agent.skills["division"](query)
        else:
            result = "未知查询类型"

        print (f"查询: {query}")
        print (f"回复: {result}")
        print ()

    

           
