# ログ追跡用 ID（traceId）とログ番号

同一リクエスト内のログをまとめて追跡するため、**1 リクエストにつき 1 つの一意 ID** を発行し、そのリクエスト中に出力されるすべてのログに同じ ID を含める。障害調査・サポート問い合わせ時に「この ID で検索」すれば、当該リクエストの一連のログを一括で取得できる。

---

## 1. ID の単位と付与方法

- **単位**: **1 HTTP リクエスト = 1 ID**（リクエストごとに 1 回だけ発行）。
- **付与**: リクエスト入口（Filter や Interceptor）で **traceId** を生成し、**MDC（Mapped Diagnostic Context）** に格納。Logback のパターンで `%X{traceId}` を指定すれば、そのリクエスト中の全ログに自動で traceId が付く。
- **レスポンスヘッダ**（任意）: クライアントが問い合わせ時に同じ ID を参照できるよう、`X-Trace-Id` 等で返すとよい。

---

## 2. traceId の形式（採用）

本プロジェクトでは **「時刻（ミリ秒まで） + 乱数 4 桁 hex」** を採用する。

| 構成 | 例 | 説明 |
|------|-----|------|
| 時刻（ミリ秒） | `20250221120000123` | `yyyyMMddHHmmssSSS` で 17 文字 |
| 乱数 4 桁 hex | `a1b2` | 小文字 16 進 4 文字 |
| **全体** | `20250221120000123a1b2` | 合計 21 文字。時刻順ソート可能。 |

同一ミリ秒内の複数リクエストは乱数部分で区別する。

---

## 3. MDC キー名

- **traceId** に統一する。ログパターン・フィルタ・APM との整合のため、プロジェクト全体で MDC キー名・ヘッダ名を `traceId` で揃える。

---

## 4. 実装例（Filter + MDC）

```java
@Component
@Order(Ordered.HIGHEST_PRECEDENCE)
public class TraceIdFilter extends OncePerRequestFilter {

    public static final String TRACE_ID_HEADER = "X-Trace-Id";
    public static final String MDC_KEY = "traceId";

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain filterChain)
            throws ServletException, IOException {
        try {
            // クライアントが既に ID を付与していればそれを使う（分散トレースの連携）、なければ新規発行
            String traceId = request.getHeader(TRACE_ID_HEADER);
            if (traceId == null || traceId.isBlank()) {
                traceId = createTraceId();
            }
            MDC.put(MDC_KEY, traceId);
            response.setHeader(TRACE_ID_HEADER, traceId);

            filterChain.doFilter(request, response);
        } finally {
            MDC.remove(MDC_KEY);
        }
    }

    /** 時刻(ミリ秒) + 4桁hex の traceId を生成。 */
    private String createTraceId() {
        String timePart = java.time.format.DateTimeFormatter.ofPattern("yyyyMMddHHmmssSSS")
                .format(java.time.LocalDateTime.now());
        String hexPart = String.format("%04x", new java.util.Random().nextInt(0x10000));
        return timePart + hexPart;
    }
}
```

---

## 5. ログ番号（log 番号）と messages.properties

`log.info` / `log.error` / `log.warn` / `log.debug` の**第 1 引数にはログ番号**を渡し、その番号をキーに **messages.properties** からメッセージ文言を取得して出力する。文言の直書きを避け、多言語対応と番号による検索を可能にする。

### 5.1 ログ番号の形式

| 部分 | 桁数 | 説明 | 例 |
|------|------|------|-----|
| **レベル** | 1 | I=INFO, E=ERROR, W=WARN, D=DEBUG | I, E, W, D |
| **業務 ID** | 3 | 業務モジュールを表す英大文字 | TOD, MEE, SYS |
| **機能 ID** | 4 | 機能・処理を表す英大文字 | CREA, UPDT, LIST, JOIN |
| **連番** | 4 | 同一機能内で 0001 から順に付与（毎回 +1） | 0001, 0002 |

**例**: `ITODCREA0001`（Info / Todo 業務 / Create 機能 / 1 番）、`ETODCREA0002`（Error / Todo 業務 / Create 機能 / 2 番）。

合計 **12 文字**。プロジェクトで業務 ID・機能 ID の一覧を決め、連番は機能ごとに採番する。

### 5.2 messages.properties との対応

- **キー** = ログ番号（例: `ITODCREA0001`）。
- **値** = メッセージテンプレート。プレースホルダは `{0}`, `{1}`（MessageSource 形式）。

```properties
# --- Todo ---
ITODCREA0001=Todo作成開始: title={0}
ITODCREA0002=Todo作成完了: id={0}
ETODCREA0001=Todo作成中にエラーが発生: title={0}
```

### 5.3 コードでの使い方

本プロジェクトでは **LogHelper**（`com.meetingtracker.support.LogHelper`）を注入し、ログ番号と引数だけを渡して出力する。LogHelper が MessageSource でメッセージを解決し、呼び出し元の Logger を自動で使用するため、**log を渡す必要はなく、@Slf4j は不要**。

**メソッドの入退場は AOP で行うため、Controller/Service の各メソッド内では入退場の logHelper を書かない。** LogHelper は **LoggingAspect**・**GlobalExceptionHandler**・および**再スローしない例外を握る箇所**（例: SSE の handleStreamError）でのみ使う。

```java
// Controller: メソッドログは AOP が出力するため、logHelper は不要
@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class TodoController {
    private final TodoService todoService;

    @PostMapping("/todos")
    public ResponseEntity<TodoResponse> createTodo(@Valid @RequestBody TodoRequest request) {
        TodoResponse response = todoService.createTodo(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }
}

// Service: ビジネスロジックのみ。例外スロー時に logCode を渡す（Handler でログ出力）
@Service
@RequiredArgsConstructor
public class TodoService {
    private final TodoMapper todoMapper;

    public TodoResponse getTodoById(String id) {
        TodoEntity todo = todoMapper.findById(id);
        if (todo == null) {
            throw new ResourceNotFoundException("Todo", "id", id, "ETODGETO0001");
        }
        return convertToResponse(todo);
    }
}
```

**GlobalExceptionHandler 内でのログ例**（例外の logCode を優先）:

```java
private void logHandledException(String defaultLogCode, Exception ex, boolean withStackTrace) {
    String logCode = (ex instanceof BusinessException bx && bx.getLogCode() != null)
            ? bx.getLogCode() : defaultLogCode;
    String msg = ex.getMessage() != null ? ex.getMessage() : ex.getClass().getSimpleName();
    if (withStackTrace) {
        logHelper.error(logCode, new Object[]{msg}, ex);
    } else {
        logHelper.error(logCode, new Object[]{msg});
    }
}
```

**ルール**:

- コード内にログ文言を直書きしない。必ずログ番号をキーに messages.properties から取得する。
- 新規ログを追加するときは、番号を採番し、messages.properties と messages_en.properties の両方に同じキーを追加する。
- Controller/Service の入退場ログは AOP に任せ、各メソッドでは logHelper を呼ばない。例外のログは Handler で行い、スロー時は `logCode` を渡す。

---

## 5.4 メソッドログは AOP で共通化

Controller/Service の **public メソッドの入退場ログ**は、各メソッド内で `logHelper.debug` / `logHelper.info` を書かず、**Spring AOP** で一括出力する。

- **Aspect**: 例として `@Around("execution(public * com.xxx.controller..*(..)) || execution(public * com.xxx.service..*(..))")` でメソッド開始・終了・所要時間をログする。
- **効果**: 入退場ログの重複を避け、Controller/Service はビジネスロジックに専念する。ログ番号は AOP 用に 1 セット（例: IASYSINV0001 / 0002 / 0003）でよい。

```java
@Aspect
@Component
@RequiredArgsConstructor
public class LoggingAspect {
    private final LogHelper logHelper;

    @Around("execution(public * com.xxx.controller..*(..)) || execution(public * com.xxx.service..*(..))")
    public Object logMethodInvocation(ProceedingJoinPoint joinPoint) throws Throwable {
        String className = joinPoint.getTarget().getClass().getSimpleName();
        String methodName = ((MethodSignature) joinPoint.getSignature()).getMethod().getName();
        logHelper.debug("IASYSINV0001", className + "." + methodName);
        long start = System.currentTimeMillis();
        try {
            Object result = joinPoint.proceed();
            logHelper.debug("IASYSINV0002", className + "." + methodName, System.currentTimeMillis() - start);
            return result;
        } catch (Throwable t) {
            logHelper.debug("IASYSINV0003", className + "." + methodName, System.currentTimeMillis() - start, t.getMessage());
            throw t;
        }
    }
}
```

---

## 5.5 例外ログは GlobalExceptionHandler に集約

**スローする例外**のログは、**GlobalExceptionHandler でのみ**出力する。業務コードでは「log してから throw」しない。

- **Handler**: 各 `@ExceptionHandler` 内で `logHelper.error(...)` を 1 回だけ呼ぶ。メッセージは null 安全（`ex.getMessage() != null ? ex.getMessage() : ex.getClass().getSimpleName()` 等）にする。
- **再スローしない例外のみ個別ログ**: 例外を catch して再スローせずに握りつぶす場合（例: SSE の `handleStreamError` でクライアントにエラー送信して完了する場合）は、その場でログ出力する。

---

## 5.6 例外のログ番号は業務コードから渡す

例外の**発生箇所をログで特定**するため、**ログ番号は Handler で固定せず、業務コードでスロー時に渡す**。

- **BusinessException 系**: コンストラクタで `logCode`（12 文字のログ番号）を受け取り、`getLogCode()` で返す。Handler では `(ex instanceof BusinessException && ex.getLogCode() != null) ? ex.getLogCode() : defaultLogCode` のように例外の logCode を優先する。
- **スロー側**: `throw new ResourceNotFoundException("Todo", "id", id, "ETODGETO0001");` のように、発生箇所ごとに異なるログ番号を渡す。Handler 側の defaultLogCode は未指定時用のフォールバックとする。

---

## 6. Logback パターン例

`logback-spring.xml` でパターンに `%X{traceId}` を入れる。

```xml
<pattern>%d{yyyy-MM-dd HH:mm:ss.SSS} [%thread] [%X{traceId}] %-5level %logger{36} - %msg%n</pattern>
```

出力例（AOP がメソッド入退場を、LogHelper が `[ログ番号] 解決済みメッセージ` 形式で出力）:

```
2025-02-21 10:00:01.123 [http-nio-8080-exec-1] [20250221100001123a1b2] DEBUG c.m.aspect.LoggingAspect - [IASYSINV0001] メソッド開始: TodoController.createTodo(...)
2025-02-21 10:00:01.125 [http-nio-8080-exec-1] [20250221100001123a1b2] DEBUG c.m.aspect.LoggingAspect - [IASYSINV0002] メソッド完了: TodoController.createTodo (15ms)
```

---

## 7. レビューチェックリスト

**traceId**

- [ ] リクエスト単位で一意の **traceId** を発行しているか（Filter 等で 1 回だけ）
- [ ] 形式は **時刻(ミリ秒 yyyyMMddHHmmssSSS) + 4 桁 hex** にしているか
- [ ] その ID を **MDC** に設定し、ログパターン（`%X{traceId}`）に含めているか
- [ ] 必要に応じてレスポンスヘッダ（`X-Trace-Id`）でクライアントに返しているか
- [ ] リクエスト終了時に **MDC.remove** でクリアしているか

**ログ番号**

- [ ] `log.info` / `log.error` 等の**第 1 引数（またはメッセージのキー）にログ番号**を使っているか
- [ ] ログ番号は **レベル(1) + 業務ID(3) + 機能ID(4) + 連番(4)** の 12 文字か
- [ ] メッセージ文言は **messages.properties** のキー（ログ番号）で定義し、直書きしていないか
- [ ] 新規ログ追加時は **messages.properties と messages_en.properties の両方**にキーを追加しているか

**メソッドログ・例外ログ**

- [ ] **メソッドログは AOP で共通化**しているか（Controller/Service の入退場を各メソッドで書いていないか）
- [ ] **例外ログは GlobalExceptionHandler に集約**しているか（業務コードで「log してから throw」していないか）
- [ ] **例外のログ番号は業務コードから渡しているか**（BusinessException に logCode を持たせ、Handler で優先利用しているか）

---

## 8. 参照

- ログレベル・出力内容: [spring-boot-best-practices.md](spring-boot-best-practices.md) の「ログ出力のベストプラクティス」
- メッセージキー命名・多言語: [exception-handling.md](exception-handling.md) の「メッセージキー」
- 機密情報をログに含めない: [security.md](security.md)
