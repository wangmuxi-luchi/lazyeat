import logging
class StateMachine:
    def __init__(self, initial_state):
        """
        初始化状态机，设置初始状态。

        :param initial_state: 初始状态
        """
        self.current_state = initial_state
        self.states = {}

    def add_state(self, state_name, process_function, entry_function=None, exit_function=None):
        """
        向状态机中添加一个状态。

        :param state_name: 状态名称
        :param process_function: 该状态对应的处理函数，返回下一个状态
        :param entry_function: 进入该状态时执行的函数
        :param exit_function: 离开该状态时执行的函数
        """
        self.states[state_name] = {
            'process': process_function,
            'entry': entry_function,
            'exit': exit_function
        }

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    def enter_state(self, state_name, args=None):
        """
        进入指定的状态。

        :param state_name: 要进入的状态名称
        """
        if self.current_state in self.states and self.states[self.current_state]['exit']:
            self.states[self.current_state]['exit']()

        if state_name in self.states:
            change_state = True
            if self.states[state_name]['entry']:
                if args:
                    change_state = self.states[state_name]['entry'](*args)
                else:
                    change_state = self.states[state_name]['entry']()
            if change_state:
                self.current_state = state_name
        else:
            print(f"状态 {state_name} 未定义。")

    def process_current_state(self, all_hands):
        """
        处理当前状态，调用对应的处理函数并跳转到下一个状态。
        调用每个状态的process函数，该函数返回下一个状态的名称，
        如果下一状态的entry函数需要参数，需要返回一个元组长度为2的元组，
        元组的第一个元素是状态名称，第二个元素是entry函数的参数组成的元组。
        """
        if self.current_state in self.states:
            process_func = self.states[self.current_state]['process']
            next_state_inf = process_func(all_hands)
            
            state_name = None
            args = None
            if  isinstance(next_state_inf, tuple) and len(next_state_inf) == 2:
                state_name, args = next_state_inf
            elif isinstance(next_state_inf, str):
                state_name = next_state_inf
            else:
                raise ValueError("next_state_inf 必须是元组或字符串")
            
            if state_name!=self.current_state:
                logging.info(f"enter_state : {state_name} args : {args}")
                self.enter_state(state_name, args)

    def get_current_state(self):
        """
        获取当前状态。

        :return: 当前状态名称
        """
        return self.current_state
