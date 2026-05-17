# レイヤーアーキテクチャルール

## 適用対象
- すべてのController、Service、Mapperクラス

## レイヤー構成

```
Controller (HTTP層)
    ↓ DTOの受け渡し
Service (ビジネスロジック層)
    ↓ Entityの受け渡し
Mapper (データアクセス層)
    ↓
Database
```

## ルール

### 1. Controller層の責任

**役割**:
- HTTPリクエスト/レスポンスの処理
- DTOのバリデーション（`@Valid`）
- Service層の呼び出し
- HTTPステータスコードの設定

**禁止事項**:
- ❌ ビジネスロジックの実装
- ❌ 直接的なデータベースアクセス
- ❌ 複雑な計算処理
- ❌ 外部API呼び出し

**✅ OK**:
```java
@PostMapping("/todos")
public ResponseEntity<TodoResponse> createTodo(@Valid @RequestBody TodoRequest request) {
    TodoResponse response = todoService.createTodo(request);
    return ResponseEntity.status(HttpStatus.CREATED).body(response);
}
```

**❌ NG**:
```java
@PostMapping("/ai/generate-todos")
public ResponseEntity<AiTodoResponse> generateTodos(@Valid @RequestBody AiGenerationRequest request) {
    // ❌ Controllerでバリデーション実施（Service層の責任）
    if (request.getApiKey() == null || request.getApiKey().trim().isEmpty()) {
        return ResponseEntity.badRequest().body(createErrorResponse("API key required"));
    }
    
    // ❌ Controllerで外部API呼び出し（Service層の責任）
    HttpPost post = new HttpPost(apiUrl);
    // ...
}
```

### 2. Service層の責任

**役割**:
- ビジネスロジックの実装
- トランザクション管理（`@Transactional`）
- データ変換（DTO ↔ Entity）
- バリデーション（ビジネスルール）
- 外部API呼び出し
- 例外処理

**禁止事項**:
- ❌ `JdbcTemplate` / `NamedParameterJdbcTemplate` の注入・利用
- ❌ SQL文字列を Service 内に直接記述して実行

**補足**:
- DBアクセスは MyBatis Mapper（`*Mapper.java` / `*Mapper.xml`）へ一元化する
- 認証・認可関連の参照処理も同様に Mapper 経由で実装する

**✅ OK**:
```java
@Service
@Transactional
public class TodoService {
    
    public TodoResponse createTodo(TodoRequest request) {
        // ビジネスルール検証
        validateBusinessRules(request);
        
        // Entity変換
        TodoEntity entity = convertToEntity(request);
        
        // データベース操作
        todoMapper.insert(entity);
        
        // Response変換
        return convertToResponse(entity);
    }
    
    private void validateBusinessRules(TodoRequest request) {
        // ビジネスルール検証はService層の責任
        if (request.getApiKey() != null && request.getApiKey().startsWith("your_")) {
            throw new ValidationException("Invalid API key format");
        }
    }
}
```

### 3. Mapper層の責任

**役割**:
- SQLの定義と実行
- データベースとの通信
- 結果のマッピング

**禁止事項**:
- ❌ ビジネスロジックの実装
- ❌ データ変換（Entity以外への変換）

### 4. 依存関係の方向

```
Controller → Service → Mapper
         ↓          ↓         ↓
        DTO      Entity    Database
```

**ルール**:
- 下位レイヤーは上位レイヤーを知らない
- Controllerは`@Autowired` でServiceを注入
- ServiceはMapperを注入
- MapperはServiceやControllerを知らない
- Controller / Service / Security / Config で `JdbcTemplate` / `NamedParameterJdbcTemplate` を注入・利用しない

## 実装パターン

### パターン1: エラーハンドリング

```java
// ❌ NG: Controllerでエラーハンドリング
@PostMapping("/api/resource")
public ResponseEntity<?> create(@RequestBody Request req) {
    try {
        return ResponseEntity.ok(service.create(req));
    } catch (Exception e) {
        return ResponseEntity.badRequest().body(e.getMessage());
    }
}

// ✅ OK: GlobalExceptionHandlerに任せる
@PostMapping("/api/resource")
public ResponseEntity<Response> create(@Valid @RequestBody Request req) {
    return ResponseEntity.ok(service.create(req));
}
```

### パターン2: バリデーション

```java
// ❌ NG: Controllerで複雑なバリデーション
@PostMapping("/api/resource")
public ResponseEntity<?> create(@RequestBody Request req) {
    if (req.getName() == null || req.getName().isEmpty()) {
        return ResponseEntity.badRequest().body("Name is required");
    }
    if (req.getAge() < 0 || req.getAge() > 150) {
        return ResponseEntity.badRequest().body("Invalid age");
    }
    // ...
}

// ✅ OK: DTOアノテーション + Service層のビジネスルール
@PostMapping("/api/resource")
public ResponseEntity<Response> create(@Valid @RequestBody Request req) {
    return ResponseEntity.ok(service.create(req));
}
```

## チェックリスト

- [ ] Controllerは HTTP 処理のみを担当している
- [ ] ビジネスロジックはすべてService層にある
- [ ] データベースアクセスはMapper層を通じて行う
- [ ] 依存関係の方向が正しい（Controller → Service → Mapper）
- [ ] 例外処理はGlobalExceptionHandlerで一元管理されている
- [ ] Controller / Service / Security / Config で `JdbcTemplate` / `NamedParameterJdbcTemplate` を使用していない
