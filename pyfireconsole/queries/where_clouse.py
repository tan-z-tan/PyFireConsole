class WhereCondition:
    def __init__(self, field, operator, value):
        self.field = field
        self.operator = operator
        self.value = value

    def to_dict(self):
        return {
            self.field: {
                self.operator: self.value
            }
        }
