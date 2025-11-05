// STUB


#[derive(Debug, Default)]
pub struct FunctionInfo {
    pub name: String,
    pub is_public: bool,
    pub signature: String,
    pub docstring: Option<String>,
}

#[derive(Debug, Default)]
pub struct ClassInfo {
    pub name: String,
    pub is_public: bool,
    pub docstring: Option<String>,
    pub methods: Vec<FunctionInfo>,
}

#[derive(Debug, Default)]
pub struct ModuleInfo {
    pub module_docstring: Option<String>,
    pub functions: Vec<FunctionInfo>,
    pub classes: Vec<ClassInfo>,
}

// stub function
pub fn parse_python_file(file_path: &str) -> anyhow::Result<ModuleInfo> {
    println!("stub of {}", file_path);

    // Повертаємо фальшиві дані, ніби ми їх розпарсили
    Ok(ModuleInfo {
        module_docstring: Some("DOCSTRING IS HERE".to_string()),
        functions: vec![
            FunctionInfo { name: "func".to_string(), is_public: true, signature: "def func(a, b)".to_string(), docstring: Some("doing someting in public".to_string()) },
            FunctionInfo { name: "_private_func".to_string(), is_public: false, ..Default::default() },
        ],
        classes: vec![
            ClassInfo {
                name: "MyPublicClass".to_string(),
                is_public: true,
                docstring: Some("some".to_string()),
                methods: vec![
                    FunctionInfo { name: "do_work".to_string(), is_public: true, signature: "do_work(self, task)".to_string(), docstring: Some("Doing work".to_string())}
                ]
            }
        ]
    })
}