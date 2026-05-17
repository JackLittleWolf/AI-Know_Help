# セキュリティルール

## 適用対象
- すべてのController、Service、Configuration クラス

## ルール

### 1. API Key / 認証情報の検証

**Service層でバリデーションを実施**:
```java
@Service
public class QWenService {
    
    public AiTodoResponse generateTodos(AiGenerationRequest request) {
        // ✅ Service層でAPI Key検証
        validateApiKey(request.getApiKey());
        
        // 処理続行
        // ...
    }
    
    private void validateApiKey(String apiKey) {
        if (apiKey == null || apiKey.isBlank()) {
            throw new ExternalApiException("API key is required");
        }
        
        if (apiKey.startsWith("your_") || apiKey.length() < 10) {
            throw new ExternalApiException("Invalid API key format");
        }
    }
}
```

### 1.1 認可（権限判定）はアノテーションを優先

**原則**:
- 権限有無の判定は `@PreAuthorize` / `@Secured` / `@RolesAllowed` を優先する
- 判定ロジックを Controller / Service 内に都度手書きしない
- メソッド単位で必要権限を明示し、生成コードでも判定位置を統一する

**❌ NG（手動判定を業務コードに分散）**:
```java
@PostMapping("/api/admin/todos")
public ResponseEntity<Void> create(@AuthenticationPrincipal UserDetails user) {
    if (!user.getAuthorities().contains(new SimpleGrantedAuthority("ROLE_ADMIN"))) {
        throw new AccessDeniedException("forbidden");
    }
    todoService.create();
    return ResponseEntity.ok().build();
}
```

**✅ OK（アノテーションで宣言的に判定）**:
```java
@PostMapping("/api/admin/todos")
@PreAuthorize("hasRole('ADMIN')")
public ResponseEntity<Void> create() {
    todoService.create();
    return ResponseEntity.ok().build();
}
```

**Service 層での適用例（推奨）**:
```java
@Service
public class TodoService {

    @PreAuthorize("hasAnyRole('ADMIN','MANAGER')")
    public void approveTodo(Long todoId) {
        // ビジネス処理
    }
}
```

**手動判定を許容する特定条件（例外）**:
- リソース所有者判定（`todo.ownerId == principal.id` のようなドメイン条件）
- 複数データソースを横断する動的権限判定（外部 ACL、テナント境界など）
- アノテーション式では表現困難な複合ルール

**例外時の実装方針**:
- 手動判定は Controller に直書きせず、`AuthorizationService` / `PermissionEvaluator` に集約する
- アノテーションと併用し、一次判定はアノテーション、詳細判定のみ集約先で実施する
- 判定失敗時は `AccessDeniedException` 等の適切な例外を使用する

**有効化設定（メソッドセキュリティ）**:
```java
@Configuration
@EnableMethodSecurity
public class MethodSecurityConfig {
}
```

### 2. CORS設定は明示的に指定

**❌ NG（セキュリティリスク）**:
```java
@Bean
public CorsFilter corsFilter() {
    CorsConfiguration config = new CorsConfiguration();
    config.setAllowedOrigins(Arrays.asList("*"));  // すべてのオリジンを許可
    config.setAllowedMethods(Arrays.asList("*"));  // すべてのメソッドを許可
    config.setAllowedHeaders(Arrays.asList("*"));  // すべてのヘッダーを許可
    // ...
}
```

**✅ OK**:
```java
@Bean
public CorsFilter corsFilter() {
    CorsConfiguration config = new CorsConfiguration();
    
    // 明示的にオリジンを指定
    config.setAllowedOrigins(Arrays.asList(
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ));
    
    // 必要なメソッドのみ許可
    config.setAllowedMethods(Arrays.asList(
        "GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"
    ));
    
    // 必要なヘッダーのみ許可
    config.setAllowedHeaders(Arrays.asList(
        "Content-Type",
        "Authorization",
        "Accept",
        "Accept-Language",
        "X-Requested-With"
    ));
    
    config.setAllowCredentials(true);
    config.setMaxAge(3600L);
    
    // ...
}
```

### 3. 環境変数で機密情報を管理

**application.properties**:
```properties
# ❌ NG: ハードコーディング
qwen.api.key=sk-abc123def456...

# ✅ OK: 環境変数から取得
qwen.api.key=${QWEN_API_KEY:}

# データベース接続情報
spring.datasource.url=${DB_URL:jdbc:sqlite:../database.sqlite}
spring.datasource.username=${DB_USERNAME:}
spring.datasource.password=${DB_PASSWORD:}
```

### 4. SQLインジェクション対策

**MyBatis でパラメータバインディングを使用**:

**❌ NG（SQLインジェクションリスク）**:
```xml
<select id="findByName" resultMap="UserResultMap">
    SELECT * FROM users WHERE name = '${name}'
</select>
```

**✅ OK**:
```xml
<select id="findByName" resultMap="UserResultMap">
    SELECT id, name, email
    FROM users 
    WHERE name = #{name}
</select>
```

### 5. XSS対策

**フロントエンドでのエスケープ**:
- HTMLコンテキストではエスケープ処理を実施
- JavaScriptコンテキストではJSON.stringifyを使用

**バックエンドでの対応**:
- `@CrossOrigin` の代わりに `CorsFilter` を使用して一元管理
- Content-Type ヘッダーを適切に設定

### 6. 機密情報のログ出力を避ける

**❌ NG**:
```java
log.info("API Key: {}", request.getApiKey());  // API Keyをログに出力
log.debug("Password: {}", user.getPassword()); // パスワードをログに出力
```

**✅ OK**:
```java
log.info("API request received for meeting: {}", request.getMeetingId());
log.debug("User authentication attempt: username={}", username);  // パスワードは出力しない
```

**マスキング処理**:
```java
private String maskApiKey(String apiKey) {
    if (apiKey == null || apiKey.length() < 8) {
        return "***";
    }
    return apiKey.substring(0, 4) + "****" + apiKey.substring(apiKey.length() - 4);
}

log.info("API request with key: {}", maskApiKey(apiKey));
```

### 7. HTTPSを使用する（本番環境）

**application-prod.properties**:
```properties
# HTTPS設定
server.ssl.enabled=true
server.ssl.key-store=classpath:keystore.p12
server.ssl.key-store-password=${SSL_KEYSTORE_PASSWORD}
server.ssl.key-store-type=PKCS12
server.ssl.key-alias=tomcat

# HTTPSへのリダイレクト
server.require-ssl=true
```

### 8. レート制限の実装（推奨）

**Bucket4j を使用した例**:
```java
@Configuration
public class RateLimitConfig {
    
    @Bean
    public Bucket createBucket() {
        Bandwidth limit = Bandwidth.classic(100, Refill.intervally(100, Duration.ofMinutes(1)));
        return Bucket.builder()
            .addLimit(limit)
            .build();
    }
}

@RestController
public class ApiController {
    
    @Autowired
    private Bucket bucket;
    
    @PostMapping("/api/resource")
    public ResponseEntity<?> create(@RequestBody Request req) {
        if (!bucket.tryConsume(1)) {
            return ResponseEntity.status(HttpStatus.TOO_MANY_REQUESTS)
                .body("Rate limit exceeded");
        }
        
        // 処理続行
        // ...
    }
}
```

### 9. 入力サイズの制限

**application.properties**:
```properties
# リクエストボディの最大サイズ
spring.servlet.multipart.max-file-size=10MB
spring.servlet.multipart.max-request-size=10MB

# HTTPヘッダーの最大サイズ
server.max-http-header-size=8KB
```

### 10. エラーメッセージに機密情報を含めない

**❌ NG**:
```java
catch (Exception e) {
    throw new RuntimeException("Database error: " + e.getMessage() + 
        ", Connection string: " + dbUrl);  // 機密情報を含む。また業務では RuntimeException を直接スローせず BusinessException を使う。
}
```

**✅ OK**:
```java
catch (Exception e) {
    log.error("Database operation failed", e);  // ログには詳細を記録
    // ユーザー向けメッセージは messages.properties のキー（例: error.database.operationFailed）で渡し、GlobalExceptionHandler で MessageSource 解決する
    throw new BusinessException("error.database.operationFailed", e);
}
```

## チェックリスト

- [ ] API Key / 認証情報の検証が実装されている
- [ ] 権限判定はアノテーション（`@PreAuthorize` など）で宣言的に実装されている
- [ ] 手動権限判定が必要な場合、判定ロジックが `AuthorizationService` / `PermissionEvaluator` に集約されている
- [ ] CORS設定が明示的で制限的である
- [ ] 機密情報は環境変数で管理されている
- [ ] SQLインジェクション対策としてパラメータバインディングを使用
- [ ] 機密情報がログに出力されていない
- [ ] 本番環境ではHTTPSを使用する設定がある
- [ ] 入力サイズの制限が設定されている
- [ ] エラーメッセージに機密情報が含まれていない
