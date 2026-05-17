# Spring Boot コーディング規約

## 適用対象
- すべての Spring Boot プロジェクト

## ルール

### 1. 依存性注入はコンストラクタインジェクションを使用

**❌ NG（フィールドインジェクション）**:
```java
@RestController
public class TodoController {
    @Autowired
    private TodoService todoService;  // テストしにくい
}
```

**✅ OK（コンストラクタインジェクション + Lombok）**:
```java
@RestController
@RequiredArgsConstructor  // Lombokでコンストラクタ自動生成
public class TodoController {
    private final TodoService todoService;  // finalで不変性を保証
}
```

**理由**:
- テスト容易性の向上（モックを簡単に注入できる）
- 不変性の保証（`final`を使用）
- 循環依存の早期検出

### 2. Lombokを活用して定型コードを削減

**活用するアノテーション**:
```java
@Data  // getter, setter, toString, equals, hashCode
@NoArgsConstructor  // デフォルトコンストラクタ
@AllArgsConstructor  // 全フィールドのコンストラクタ
@RequiredArgsConstructor  // final/非nullフィールドのコンストラクタ
@Builder  // ビルダーパターン
@Slf4j  // ログ出力（※ログは LogHelper を使う場合は Controller/Service では不要）
```

**DTO の例**:
```java
@Data
@NoArgsConstructor
@AllArgsConstructor
public class TodoRequest {
    private String meetingId;
    private String title;
    private String description;
}
```

**Service の例**（ログは LogHelper を注入し、ログ番号で出力）:
```java
@Service
@RequiredArgsConstructor
public class TodoService {
    private final TodoMapper todoMapper;
    private final LogHelper logHelper;

    public void process() {
        logHelper.info("ITODCREA0001", "Processing started");
    }
}
```

### 3. 例外処理は`@ControllerAdvice`で一元管理

**GlobalExceptionHandler の実装**（ログは LogHelper、ユーザー向けメッセージは MessageSource、レスポンス形式は API 仕様に準拠）:
```java
@RestControllerAdvice
@RequiredArgsConstructor
public class GlobalExceptionHandler {
    private final MessageSource messageSource;
    private final LogHelper logHelper;

    @ExceptionHandler(ResourceNotFoundException.class)
    public ResponseEntity<ErrorResponse> handleResourceNotFound(ResourceNotFoundException ex, Locale locale) {
        logHelper.error("ESYSNOTF0002", new Object[]{ex.getMessage()});
        String message = ex.getMessageKey() != null
                ? messageSource.getMessage(ex.getMessageKey(), ex.getMessageArgs(), locale)
                : ex.getMessage();
        return ResponseEntity.status(HttpStatus.NOT_FOUND)
                .body(ErrorResponse.builder()
                        .timestamp(OffsetDateTime.now().toString())
                        .status(HttpStatus.NOT_FOUND.value())
                        .error("Not Found")
                        .message(message)
                        .build());
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErrorResponse> handleValidationException(MethodArgumentNotValidException ex, Locale locale) {
        logHelper.error("ESYSVALI0001", ex.getMessage());
        Map<String, String> details = new HashMap<>();
        ex.getBindingResult().getAllErrors().forEach(err -> {
            String field = ((FieldError) err).getField();
            details.put(field, err.getDefaultMessage());
        });
        String message = messageSource.getMessage("validation.failed", null, locale);
        return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                .body(ErrorResponse.builder()
                        .timestamp(OffsetDateTime.now().toString())
                        .status(HttpStatus.BAD_REQUEST.value())
                        .error("Validation Failed")
                        .message(message)
                        .details(details)
                        .build());
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handleGenericException(Exception ex, Locale locale) {
        logHelper.error("ESYSINTR0001", new Object[]{ex.getMessage()}, ex);
        String message = messageSource.getMessage("error.internal", null, locale);
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(ErrorResponse.builder()
                        .timestamp(OffsetDateTime.now().toString())
                        .status(HttpStatus.INTERNAL_SERVER_ERROR.value())
                        .error("Internal Server Error")
                        .message(message)
                        .build());
    }
}
```
例外の種類ごとの詳細（ResourceNotFoundException / ExternalApiException / BusinessException 等）は [exception-handling.md](exception-handling.md) を参照。

### 4. トランザクション管理は`@Transactional`を使用

**Service層でトランザクション管理**:
```java
@Service
@Transactional  // クラスレベル：すべてのpublicメソッドがトランザクション対象
public class TodoService {
    
    // このメソッドは自動的にトランザクション内で実行される
    public TodoResponse createTodo(TodoRequest request) {
        TodoEntity entity = convertToEntity(request);
        todoMapper.insert(entity);
        return convertToResponse(entity);
    }
    
    // 読み取り専用トランザクション（パフォーマンス最適化）
    @Transactional(readOnly = true)
    public List<TodoResponse> getTodos(String meetingId) {
        return todoMapper.findByMeetingId(meetingId).stream()
            .map(this::convertToResponse)
            .collect(Collectors.toList());
    }
}
```

### 5. REST APIのベストプラクティス

**HTTPメソッドの使い分け**:
```java
@RestController
@RequestMapping("/api/todos")
@RequiredArgsConstructor
public class TodoController {
    
    // GET: リソースの取得
    @GetMapping
    public ResponseEntity<List<TodoResponse>> getTodos() {
        return ResponseEntity.ok(todoService.getTodos());
    }
    
    @GetMapping("/{id}")
    public ResponseEntity<TodoResponse> getTodo(@PathVariable String id) {
        return ResponseEntity.ok(todoService.getTodo(id));
    }
    
    // POST: 新規リソースの作成
    @PostMapping
    public ResponseEntity<TodoResponse> createTodo(@Valid @RequestBody TodoRequest request) {
        TodoResponse response = todoService.createTodo(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }
    
    // PUT: リソース全体の更新
    @PutMapping("/{id}")
    public ResponseEntity<TodoResponse> updateTodo(
            @PathVariable String id,
            @Valid @RequestBody TodoRequest request) {
        return ResponseEntity.ok(todoService.updateTodo(id, request));
    }
    
    // PATCH: リソースの部分更新
    @PatchMapping("/{id}")
    public ResponseEntity<TodoResponse> patchTodo(
            @PathVariable String id,
            @RequestBody Map<String, Object> updates) {
        return ResponseEntity.ok(todoService.patchTodo(id, updates));
    }
    
    // DELETE: リソースの削除
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteTodo(@PathVariable String id) {
        todoService.deleteTodo(id);
        return ResponseEntity.noContent().build();
    }
}
```

**HTTPステータスコードの使い分け**:
- `200 OK`: 成功（GET, PUT, PATCH）
- `201 Created`: 新規作成成功（POST）
- `204 No Content`: 成功（レスポンスボディなし）（DELETE）
- `400 Bad Request`: 入力エラー
- `404 Not Found`: リソースが見つからない
- `500 Internal Server Error`: サーバーエラー

### 6. プロパティファイルの管理

**application.properties の構成**:
```properties
# アプリケーション基本設定
spring.application.name=meeting-tracker
server.port=8080

# データソース
spring.datasource.url=${DB_URL:jdbc:sqlite:../database.sqlite}
spring.datasource.driver-class-name=org.sqlite.JDBC

# MyBatis
mybatis.mapper-locations=classpath:mapper/*.xml
mybatis.type-aliases-package=com.meetingtracker.entity
mybatis.configuration.map-underscore-to-camel-case=true

# 外部API
qwen.api.key=${QWEN_API_KEY:}
qwen.api.url=https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation
qwen.api.timeout=30000
```

**環境別設定ファイル**:
- `application.properties`: 共通設定
- `application-dev.properties`: 開発環境
- `application-prod.properties`: 本番環境

### 7. ログ出力のベストプラクティス

**追跡用 ID（traceId）**: 1 リクエストにつき 1 つの一意 ID を発行し、そのリクエスト内の全ログに同じ ID を付与する。形式は **時刻(ミリ秒 yyyyMMddHHmmssSSS) + 4 桁 hex**。実装例（Filter + MDC）・ログ番号・Logback パターンは [logging.md](logging.md) を参照。

**ログは LogHelper を使用**（log を渡さず、ログ番号＋引数のみ。文言は messages.properties で定義）:
```java
@Service
@RequiredArgsConstructor
public class TodoService {
    private final TodoMapper todoMapper;
    private final LogHelper logHelper;

    public TodoResponse createTodo(TodoRequest request) {
        logHelper.info("ITODCREA0001", request.getTitle());

        try {
            TodoEntity entity = convertToEntity(request);
            todoMapper.insert(entity);
            logHelper.debug("DTODCREA0001", entity.getId());
            logHelper.info("ITODCREA0002", entity.getId());
            return convertToResponse(entity);
        } catch (Exception e) {
            logHelper.error("ETODCREA0001", request.getTitle(), e);
            throw new BusinessException("todo.save.failed", e);
        }
    }

    public void validateTodo(TodoRequest request) {
        if (request.getPriority() == null) {
            logHelper.warn("WTODVALI0001", request.getTitle());
        }
    }
}
```
- **INFO**: 重要な業務の開始/完了 → `logHelper.info("番号", args)`
- **DEBUG**: 詳細な処理状況 → `logHelper.debug("番号", args)`
- **WARN**: 注意が必要だが継続 → `logHelper.warn("番号", args)`
- **ERROR**: エラー（Throwable 付き可）→ `logHelper.error("番号", args)` または `logHelper.error("番号", t)`
- ログ番号は 12 文字（レベル 1 + 業務 ID 3 + 機能 ID 4 + 連番 4）。messages.properties / messages_en.properties にキーを追加する。詳細は [logging.md](logging.md)。

### 8. Bean のスコープとスレッドセーフティ

**デフォルトは Singleton**（複数スレッドで同一インスタンスを共有するため、**可変のインスタンス変数を持たないこと**）:
```java
@Service  // デフォルトでSingleton
public class TodoService {
    // アプリケーション全体で1つのインスタンスのみ。可変フィールドがあると並行アクセスで不具合の原因になる。
}
```

詳細は [thread-safety.md](thread-safety.md) を参照（Singleton + 可変インスタンス変数 = スレッド不安全のリスク）。

**状態を持つ場合は Prototype**:
```java
@Service
@Scope("prototype")  // リクエストごとに新しいインスタンスを作成
public class StatefulService {
    private String state;  // 状態を持つ
}
```

### 9. カスタムプロパティの使用

**プロパティクラスの定義**:
```java
@ConfigurationProperties(prefix = "qwen.api")
@Validated
@Data
public class QWenApiProperties {
    @NotBlank
    private String key;
    
    @NotBlank
    private String url;
    
    @NotNull
    private Integer timeout;
}
```

**有効化**:
```java
@Configuration
@EnableConfigurationProperties(QWenApiProperties.class)
public class AppConfig {
}
```

**使用**:
```java
@Service
@RequiredArgsConstructor
public class QWenService {
    private final QWenApiProperties properties;
    
    public void callApi() {
        String apiUrl = properties.getUrl();
        // ...
    }
}
```

### 10. データアクセス方針（必須）

**方針**:
- DBアクセスは MyBatis Mapper（`*Mapper.java` / `*Mapper.xml`）へ一元化する
- Controller / Service / Security / Config に `JdbcTemplate` / `NamedParameterJdbcTemplate` を注入しない

**❌ NG**:
```java
@Service
@RequiredArgsConstructor
public class UserPermissionService {
    private final JdbcTemplate jdbcTemplate;

    public List<String> loadPermissions(String role) {
        return jdbcTemplate.query("SELECT code FROM permissions WHERE role = ?",
                (rs, rowNum) -> rs.getString("code"), role);
    }
}
```

**✅ OK**:
```java
@Service
@RequiredArgsConstructor
public class UserPermissionService {
    private final UserPermissionMapper userPermissionMapper;

    public List<String> loadPermissions(String role) {
        return userPermissionMapper.findPermissionCodesByRole(role);
    }
}
```

## チェックリスト

- [ ] コンストラクタインジェクションを使用している
- [ ] Lombokで定型コードを削減している
- [ ] 例外処理が`@ControllerAdvice`で一元管理されている
- [ ] トランザクション管理に`@Transactional`を使用している
- [ ] REST APIのHTTPメソッドとステータスコードが適切
- [ ] 環境変数で機密情報を管理している
- [ ] ログレベルが適切に使い分けられている
- [ ] Beanのスコープが適切に設定されている
- [ ] DBアクセスが MyBatis Mapper に一元化され、Controller / Service / Security / Config で `JdbcTemplate` / `NamedParameterJdbcTemplate` を使用していない
