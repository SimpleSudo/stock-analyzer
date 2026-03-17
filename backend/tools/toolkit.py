from .akshare_tools import AkshareTools

class Toolkit:
    """
    工具箱：统一管理所有外部数据获取工具，供 Agent 调用。
    这样 Agent 不需要直接知道具体的实现，只需要通过工具名获取对应的工具方法。
    """
    def __init__(self):
        self.akshare = AkshareTools()
        # 可以在这里添加其他工具，例如新闻工具、宏观经济工具等

    # 为了便于 Agent 调用，我们可以提供一些常用的方法，或者直接暴露 akshare 对象
    # 这里我们提供一个通用的调用方式：通过工具名和方法名来调用
    # 但为了简单起见，我们直接让 Agent 访问 self.akshare 来调用具体方法。
    # 例如: toolkit.akshare.get_stock_hist(symbol)

    # 如果以后有多种工具来源，可以这样设计：
    # def get_tool(self, tool_name: str):
    #     if tool_name == "akshare":
    #         return self.akshare
    #     # ... 其他工具
    #     else:
    #         raise ValueError(f"Unknown tool: {tool_name}")
