# Tree-sitter C# Node Types - Hướng dẫn cho người mới

Tài liệu này giải thích chi tiết các NodeTypes mà tree-sitter C# grammar hỗ trợ, được sử dụng trong Code-Graph-RAG để phân tích code C#.

## Mục lục

1. [Tổng quan](#tổng-quan)
2. [Declarations (Khai báo)](#declarations-khai-báo)
3. [Expressions (Biểu thức)](#expressions-biểu-thức)
4. [Statements (Câu lệnh)](#statements-câu-lệnh)
5. [Patterns (Mẫu)](#patterns-mẫu)
6. [Types (Kiểu dữ liệu)](#types-kiểu-dữ-liệu)
7. [Query Expressions (LINQ)](#query-expressions-linq)
8. [Xử lý NodeTypes trong Code-Graph-RAG](#xử-lý-nodeypes-trong-code-graph-rag)

---

## Tổng quan

### NodeType là gì?

**NodeType** là tên của node trong AST (Abstract Syntax Tree) được tạo ra bởi tree-sitter parser. Mỗi node đại diện cho một cấu trúc ngữ pháp trong code.

Ví dụ:
```csharp
// Code C#
public void HelloWorld() { }
// AST từ tree-sitter:
// class_declaration
//   modifier: "public"
//   method_declaration
//     identifier: "HelloWorld"
//     parameter_list: "()"
//     block: "{ }"
```

### Tại sao cần hiểu NodeTypes?

1. **Phân tích code**: Xác định các thành phần trong codebase
2. **Tạo relationships**: Xây dựng CALLS, IMPORTS, DEFINES relationships
3. **Type inference**: Suy luận kiểu dữ liệu
4. **Code navigation**: Navigate đến definitions, references

---

## Declarations (Khai báo)

### Class & Type Declarations

#### `class_declaration`
Khai báo class.

```csharp
public class MyClass { }
```
```
class_declaration
├── modifier: "public"
├── identifier: "MyClass"
└── declaration_list: "{ }"
```

#### `interface_declaration`
Khai báo interface.

```csharp
public interface IRepository { }
```

#### `struct_declaration`
Khai báo struct (value type).

```csharp
public struct Point { public int X; public int Y; }
```

#### `record_declaration`
Khai báo record (C# 9.0+).

```csharp
public record Person(string Name, int Age);
```

#### `enum_declaration`
Khai báo enum.

```csharp
public enum Status { Active, Inactive, Pending }
```

#### `delegate_declaration`
Khai báo delegate.

```csharp
public delegate void EventHandler(object sender, EventArgs e);
```

### Member Declarations

#### `method_declaration`
Khai báo method.

```csharp
public int Calculate(int a, int b) { return a + b; }
```
```
method_declaration
├── modifier: "public"
├── predefined_type: "int"
├── identifier: "Calculate"
├── parameter_list
│   ├── parameter
│   │   ├── predefined_type: "int"
│   │   └── identifier: "a"
│   └── parameter (b)
└── block: "{ ... }"
```

#### `constructor_declaration`
Khai báo constructor.

```csharp
public MyClass(string name) { Name = name; }
```

#### `destructor_declaration`
Khai báo destructor.

```csharp
~MyClass() { /* cleanup */ }
```

#### `property_declaration`
Khai báo property.

```csharp
public string Name { get; set; }
```

#### `indexer_declaration`
Khai báo indexer.

```csharp
public int this[int index] { get; set; }
```

#### `field_declaration`
Khai báo field.

```csharp
private int _count;
```

#### `event_declaration`
Khai báo event.

```csharp
public event EventHandler OnChanged;
```

#### `operator_declaration`
Khai báo operator overload.

```csharp
public static MyClass operator +(MyClass a, MyClass b) { ... }
```

#### `conversion_operator_declaration`
Khai báo implicit/explicit conversion.

```csharp
public static implicit operator int(MyClass value) { return value.Value; }
```

### Namespace & Imports

#### `namespace_declaration`
Khai báo namespaceblock-scoped.

```csharp
namespace MyCompany.MyProduct { }
```

#### `file_scoped_namespace_declaration`
Khai báo namespace file-scoped (C# 10+).

```csharp
namespace MyCompany.MyProduct;
// Rest of file
```

#### `using_directive`
Import namespace hoặctype.

```csharp
using System;
using static System.Math;
using MyAlias = MyCompany.MyProduct.MyClass;
```

---

## Expressions (Biểu thức)

### Call & Invocation Expressions

#### `invocation_expression`
**⭐ Quan trọng**: Tạo CALLS relationships.

```csharp
Console.WriteLine("Hello");
obj.Method();
```
```
invocation_expression
├── member_access_expression
│   ├── identifier: "Console"
│   └── identifier: "WriteLine"
└── argument_list
    └── argument: "\"Hello\""
```

**Xử lý trong Code-Graph-RAG**:
- Được xử lý bởi `call_processor.py`
- Tạo CALLS relationship đến target method/function

#### `object_creation_expression`
**⭐ Quan trọng**: Constructor call.

```csharp
var obj = new MyClass();
var list = new List<int> { 1, 2, 3 };
```

#### `implicit_object_creation_expression`
Object creation không cần type (C# 9+).

```csharp
MyClass obj = new(); // Type inference
```

#### `anonymous_object_creation_expression`
Anonymous type creation.

```csharp
var person = new { Name = "John", Age = 30 };
```

### Member Access Expressions

#### `member_access_expression`
**⭐ Quan trọng**: Property/Method access.

```csharp
obj.Property
obj.Method()
```

#### `element_access_expression`
Array/Collection indexer access.

```csharp
array[0]
dict["key"]
```

#### `conditional_access_expression`
Null-conditional access (C# 6+).

```csharp
obj?.Property
obj?.Method()
```

### Lambda & Anonymous Functions

#### `lambda_expression`
Lambda expression.

```csharp
(x, y) => x + y
(Func<int, int, int>)((x, y) => x + y)
```
```
lambda_expression
├── parameter_list: "x, y"
└── block_or_expression: "x + y"
```

#### `anonymous_method_expression`
Anonymous method (delegate).

```csharp
delegate(int x) { return x * 2; }
```

### Type-Related Expressions

#### `cast_expression`
Type casting.

```csharp
int value = (int)doubleValue;
```

#### `as_expression`
**Issue #26**: Type conversion với null nếu thất bại.

```csharp
MyClass? obj = unknown as MyClass;
```

#### `is_expression`
**Issue #26**: Type checking.

```csharp
if (obj is MyClass) { }
if (obj is MyClass c) { } // Pattern matching
```

#### `typeof_expression`
Get type metadata.

```csharp
Type t = typeof(MyClass);
```

#### `sizeof_expression`
Get size of type.

```csharp
int size = sizeof(int);
```

#### `default_expression`
Default value of type.

```csharp
int? value = default(int);
```

### Control Flow Expressions

#### `conditional_expression`
**Issue #26**: Ternary operator.

```csharp
var result = condition ? trueValue : falseValue;
```

#### `switch_expression`
Switch expression (C# 8+).

```csharp
var result = value switch
{
    1 => "one",
    2 => "two",
    _ => "other"
};
```

### Assignment & Operators

#### `assignment_expression`
Assignment với operators.

```csharp
x = 1
x += 1
x ??= defaultValue
```

#### `binary_expression`
Binary operators.

```csharp
a + b
a && b
a == b
a ?? b // Null coalescing
```

#### `prefix_unary_expression`
Unary prefix operators.

```csharp
-x
!flag
++i
--i
```

#### `postfix_unary_expression`
Unary postfix operators.

```csharp
i++
i--
```

### Collection Expressions

#### `initializer_expression`
**Issue #26**: Object/Collection initializer.

```csharp
new List<int> { 1, 2, 3 }
new MyClass { Name = "John", Age = 30 }
```

#### `array_creation_expression`
Array creation.

```csharp
new int[] { 1, 2, 3 }
new int[10]
```

#### `implicit_array_creation_expression`
Implicitly typed array.

```csharp
var arr = new[] { 1, 2, 3 };
```

#### `stackalloc_expression`
**Issue #26**: Stack allocation.

```csharp
Span<int> span = stackalloc int[100];
```

#### `implicit_stackalloc_expression`
**Issue #26**: Implicit stackalloc.

```csharp
Span<int> span = stackalloc[] { 1, 2, 3 };
```

### Special Expressions

#### `await_expression`
Await expression.

```csharp
var result = await task;
```

#### `throw_expression`
Throw expression (C# 7+).

```csharp
var obj = GetObject() ?? throw new Exception("Null");
```

#### `with_expression`
Record modification (C# 9+).

```csharp
var person2 = person1 with { Age = 31 };
```

#### `range_expression`
Range expression (C# 8+).

```csharp
var slice = array[1..^1];
```

#### `interpolated_string_expression`
String interpolation.

```csharp
$"Hello, {name}!"
```

#### `tuple_expression`
Tuple creation.

```csharp
var tuple = (1, "text", true);
```

### Low-level Expressions

#### `ref_expression`
Reference expression.

```csharp
ref int x = ref arr[0];
```

#### `ref_type`
Check if type is reference.

```csharp
bool isRef = __reftype(obj) == typeof(string);
```

#### `refvalue_expression`
Get ref value.

```csharp
ref string s = ref __refvalue(obj, string);
```

#### `makeref_expression`
Create typed reference.

```csharp
var tref = __makeref(obj);
```

---

## Statements (Câu lệnh)

### Control Flow Statements

#### `if_statement`
If statement.

```csharp
if (condition) { }
else if (other) { }
else { }
```

#### `switch_statement`
Switch statement.

```csharp
switch (value)
{
    case 1: break;
    case 2: break;
    default: break;
}
```

#### `for_statement`
For loop.

```csharp
for (int i = 0; i < 10; i++) { }
```

#### `foreach_statement`
Foreach loop.

```csharp
foreach (var item in collection) { }
```

#### `while_statement`
While loop.

```csharp
while (condition) { }
```

#### `do_statement`
Do-while loop.

```csharp
do { } while (condition);
```

### Jump Statements

#### `return_statement`
Return statement.

```csharp
return;
return value;
```

#### `break_statement`
Break from loop.

```csharp
while (true) { if (x) break; }
```

#### `continue_statement`
Continue to next iteration.

```csharp
foreach (var item in items) { if (skip) continue; }
```

#### `goto_statement`
Goto statement.

```csharp
goto Label;
Label: ;
```

#### `throw_statement`
Throw exception.

```csharp
throw new Exception("Error");
```

### Exception Handling

#### `try_statement`
Try-catch-finally.

```csharp
try { }
catch (Exception ex) { }
finally { }
```

### Resource Management

#### `using_statement`
Resource management (IDisposable).

```csharp
using (var resource = new Resource()) { }
using var resource = new Resource(); // C# 8+
```

#### `lock_statement`
Thread synchronization.

```csharp
lock (lockObject) { }
```

#### `fixed_statement`
Pointer fixed (unsafe).

```csharp
fixed (int* p = &arr[0]) { }
```

#### `unsafe_statement`
Unsafe block.

```csharp
unsafe { /* pointer operations */ }
```

### Checked/Unchecked

#### `checked_statement`
**Issue #26**: Checked arithmetic block.

```csharp
checked
{
    int result = int.MaxValue + 1; // OverflowException
}
```

**Lưu ý**: Không tạo CALLS relationships. Tree-sitter tự động traverse vào children.

#### `checked_expression`
Checked expression.

```csharp
int result = checked(a + b);
```

### Other Statements

#### `local_declaration_statement`
Variable declaration.

```csharp
var x = 1;
int y = 2;
MyClass obj = new();
```

#### `local_function_statement`
Local function (C# 7+).

```csharp
void LocalFunction() { }
```

#### `expression_statement`
Expression as statement.

```csharp
Console.WriteLine("Hello"); // invocation expression
x++; // postfix increment
```

#### `empty_statement`
Empty statement.

```csharp
; // Empty statement
```

#### `labelled_statement`
Label for goto.

```csharp
Label:
goto Label;
```

#### `yield_statement`
Yield for iterator.

```csharp
yield return value;
yield break;
```

---

## Patterns (Mẫu)

Pattern matching đượcintroduce trong C# 7+ và mở rộng trong các version sau.

### Basic Patterns

#### `constant_pattern`
Match constant value.

```csharp
if (obj is 1) { }  // Object pattern
switch (value) { case 0: break; }  // Switch pattern
```

#### `type_pattern`
Match type.

```csharp
if (obj is int i) { }
if (obj is List<string>) { }
```

#### `var_pattern`
Var pattern (always matches).

```csharp
if (obj is var x) { }  // Always matches
```

### Composed Patterns

#### `and_pattern`
AND pattern (C# 9+).

```csharp
if (obj is >0 and <100) { }
```

#### `or_pattern`
OR pattern (C# 9+).

```csharp
if (obj is 1 or 2 or 3) { }
```

#### `negated_pattern`
NOT pattern (C# 9+).

```csharp
if (obj is not null) { }
```

#### `parenthesized_pattern`
Parenthesized pattern.

```csharp
if (obj is (int and >0)) { }
```

### Complex Patterns

#### `recursive_pattern`
Recursive pattern (property/positional).

```csharp
if (obj is Point { X: >0, Y: >0 }) { }  // Property pattern
if (obj is Point(int x, int y)) { }      // Positional pattern
```

#### `property_pattern_clause`
Property pattern.

```csharp
if (obj is Person { Name: "John", Age: >18 }) { }
```

#### `positional_pattern_clause`
Positional pattern.

```csharp
if (obj is (int x, string y)) { }
```

#### `list_pattern`
List pattern (C# 11+).

```csharp
if (arr is [1, 2, 3]) { }
if (arr is [var first, .., var last]) { }  // Slice pattern
```

#### `relational_pattern`
Relational pattern (C# 9+).

```csharp
switch (value)
{
    case >0 and <10: break;
    case >=10 and <100: break;
}
```

---

## Query Expressions (LINQ)

### `query_expression`
**Issue #26**: LINQ query syntax.

```csharp
var result = from n in numbers
             where n > 0
             select n * 2;
```

**AST Structure:**
```
query_expression
├── from_clause
│   ├── identifier: "n"
│   └── identifier: "numbers"
├── where_clause
│   └── binary_expression: "n > 0"
└── select_clause
    └── binary_expression: "n * 2"
```

**Lưu ý quan trọng:**
- LINQ query syntax được convert thành method calls bởi compiler
- `from ... where ... select` → `.Where(...).Select(...)`
- Trong AST, đây là clause hierarchy, không phải invocation
- **Không tạo CALLS relationships trực tiếp**
- Nếu cần phân tích LINQ connections, cần semantic analysis riêng

---

## Types (Kiểu dữ liệu)

### Type Nodes trong tree-sitter C#

Tree-sitter C# sử dụng nhiều node types để biểu diễn types:

#### Primitive Types
```
predefined_type: "int", "string", "bool", "void", etc.
```

#### Complex Types
```
qualified_name: "System.Collections.Generic.List"
generic_name: "List<int>"
array_type: "int[]"
pointer_type: "int*"
nullable_type: "int?"
tuple_type: "(int, string)"
ref_type: "ref int"
```

#### Type Parameters
```
type_parameter: "T"where class Foo<T> where T : class
```

---

## Xử lý NodeTypes trong Code-Graph-RAG

### NodeTypes tạo CALLS Relationships

| NodeType | Tạo CALLS? | Ghi chú |
|----------|-----------|---------|
| `invocation_expression` | ✅ Yes | Method/function calls |
| `object_creation_expression` | ✅ Yes | Constructor calls |
| `implicit_object_creation_expression` | ✅ Yes | Constructor calls (type inference) |
| `anonymous_object_creation_expression` | ❌ No | Anonymous type, no named constructor |
| Member access (`member_access_expression`) | ❌ No | Chỉ access, không phải call. Tuy nhiên, thường là target của invocation |

### NodeTypesKHÔNG tạo CALLS (chỉ traverse)

| NodeType | Lý do không tạo CALLS |
|----------|----------------------|
| `checked_statement` | Block statement, tree-sitter traverse children |
| `as_expression` | Type conversion, không phải call |
| `is_expression` | Type checking, không phải call |
| `conditional_expression` | Ternary operator, điều khiển flow |
| `initializer_expression` | Object/collection initializer |
| `stackalloc_expression` | Memory allocation |
| `query_expression` | LINQ query syntax, cần semantic analysis |

### Quy tắc xử lý NodeTypes

1. **Invocation nodes** (`invocation_expression`, `object_creation_expression`):
   - Tạo CALLS relationship đến target method/constructor
   - Xử lý bởi `call_processor.py`

2. **Block/Container nodes** (`checked_statement`, `unsafe_statement`):
   - Tree-sitter tự động traverse vào children
   - Không cần xử lý đặc biệt

3. **Type-related nodes** (`as_expression`, `is_expression`, `cast_expression`):
   - Xử lý bởi `type_inference.py`
   - Giúp suy luận kiểu dữ liệu

4. **Query expression** (`query_expression`):
   - LINQ query syntax là syntactic sugar
   - Không tạo CALLS trực tiếp trong AST
   - Cần semantic analysis để transform thành method calls

---

## Testing NodeTypes

### Test trong `test_class_ingest.py`

```python
def test_csharp_invocation():
    """Test invocation_expression tạo CALLS."""
    code = """
    public class Test {
        public void Method() {
            Console.WriteLine("Hello");
        }
    }
    """
    # Assert: invocation_expression tạo CALLS đến Console.WriteLine

def test_csharp_checked_statement():
    """Test checked_statement traverse children."""
    code = """
    public class Test {
        public void Method() {
            checked {
                int result = int.MaxValue + 1;
            }
        }
    }
    """
    # Assert: checked_statement không tạo CALLS
    # Child expressions được traverse bình thường
```

---

## Tài liệu tham khảo

1. **Tree-sitter C# Grammar**: https://github.com/tree-sitter/tree-sitter-c-sharp
2. **C# Language Specification**: https://docs.microsoft.com/en-us/dotnet/csharp/
3. **Code-Graph-RAG Implementation**:
   - `constants.py`: NodeTypes definitions
   - `parsers/call_processor.py`: CALLS processing
   - `parsers/csharp/type_inference.py`: Type inference

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-03-29 | Initial documentation |
| 1.1 | 2025-03-29 | Added Issue #26 NodeTypes (checked_statement, as/is_expression, etc.) |
