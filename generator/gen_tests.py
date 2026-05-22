
#!/usr/bin/env python3
# generator/gen_tests.py
import yaml
import os
from pathlib import Path
from typing import Dict, List, Any

# 1. ШАБЛОНЫ КОДА (f-strings). Двойные {{}} экранируют фигурные скобки для C#
TEST_FILE_TEMPLATE = """//
// AUTO-GENERATED TESTS. DO NOT EDIT MANUALLY.
// Source: {spec_source}
// Generator: gen_tests.py v1.0
//
using System;
using System.Collections.Generic;
using NUnit.Framework;
using Lab.Interfaces;

namespace Module.Tests
{{
    [TestFixture]
    [Description("Автоматически сгенерированные тесты для {module_name}")]
    public class {module_name}Tests
    {{
        private I{module_name} _sut;

        [SetUp]
        public void SetUp()
        {{
            // Инициализация тестируемой системы (SUT)
            // В реальном проекте здесь будет создание конкретного класса, например: new ToDoListManager();
        }}

{test_methods}
    }}
}}
"""

TEST_METHOD_TEMPLATE = """
        [Test]
        [Description("Класс эквивалентности: {case_desc}")]
{test_cases}
        public void Test_{method_name}_{case_name}()
        {{
            // === Arrange ===
            // Предусловие (Precondition): {pre}
            // Ожидаемый результат: {expected}

            // === Act ===
            {act_code}

            // === Assert ===
            // Постусловие (Postcondition): {post}
            {assert_code}
        }}
"""

TEST_CASE_TEMPLATE = "        [TestCase({inputs})]"

# 2. ПАРСИНГ СПЕЦИФИКАЦИИ
def load_spec(spec_path: str) -> Dict[str, Any]:
    with open(spec_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# 3. ГЕНЕРАЦИЯ КОДА
def format_csharp_input(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, str):
        return f'"{value}"'
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)

def generate_method_tests(method_data: Dict[str, Any]) -> List[str]:
    case_blocks = []
    method_name = method_data["name"]
    
    for eq_class in method_data.get("equivalence_classes", []):
        # Формируем входные параметры для [TestCase]
        inputs_str = ", ".join(format_csharp_input(inp) for inp in eq_class["inputs"])
        
        # Формируем Act-код (вызов метода)
        if method_data["signature"].startswith("void"):
            act_code = f"_sut.{method_name}({inputs_str});"
        else:
            act_code = f"var result = _sut.{method_name}({inputs_str});"
            
        # Формируем Assert-заглушку по методичке
        assert_code = 'Assert.Pass("Generated assertion placeholder. Replace with actual logic based on postcondition.");'
        
        # Безопасное имя метода без пробелов и спецсимволов
        safe_case_name = eq_class["case"].replace(" ", "_").replace("(", "").replace(")", "").replace("'", "")
        
        # Собираем блок тест-метода
        method_code = TEST_METHOD_TEMPLATE.format(
            case_desc=eq_class["case"],
            test_cases=TEST_CASE_TEMPLATE.format(inputs=inputs_str) if inputs_str else "        // No inputs",
            method_name=method_name,
            case_name=safe_case_name,
            pre=method_data["pre"],
            expected=eq_class["expected"],
            act_code=act_code,
            post=method_data["post"],
            assert_code=assert_code
        )
        case_blocks.append(method_code)
        
    return case_blocks

def render_and_save(spec: Dict[str, Any], config: Dict[str, Any]) -> None:
    module_name = spec["module"]
    test_methods = []
    
    for method in spec["methods"]:
        test_methods.extend(generate_method_tests(method))
        
    tests_block = "".join(test_methods)
    
    file_content = TEST_FILE_TEMPLATE.format(
        spec_source=config.get("spec_path", "N/A"),
        module_name=module_name,
        test_methods=tests_block
    )
    
    out_dir = Path(config.get("output_dir", "tests/Module.Tests"))
    out_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = out_dir / f"{module_name}Tests.Generated.cs"
    output_file.write_text(file_content, encoding="utf-8")
    
    print(f"[√] Сгенерирован файл: {output_file}")
    print(f"    Методов покрыто: {len(spec['methods'])}")
    print(f"    Тестов сгенерировано: {sum(len(m.get('equivalence_classes', [])) for m in spec['methods'])}")

# 4. ТОЧКА ВХОДА
if __name__ == "__main__":
    config_path = "config.yaml"
    print("[*] Загрузка конфигурации...")
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        
    print(f"[*] Загрузка спецификации: {config['spec_path']}...")
    spec_data = load_spec(config["spec_path"])
    
    print("[*] Генерация C# тестов...")
    render_and_save(spec_data, config)
    print("[√] Готово.")
