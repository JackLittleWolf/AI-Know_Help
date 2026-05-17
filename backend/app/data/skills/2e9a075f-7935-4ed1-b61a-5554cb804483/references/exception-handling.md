# 例外処理の統一ルール

本プロジェクト全体で例外を扱う際に守る共通ルール。Backend・Frontend・API の一貫した振る舞いを定める。

---

## 1. 基本方針

- **Controller 層では例外を catch しない。** 発生した例外はすべて `GlobalExceptionHandler` で捕捉し、HTTP レスポンスに変換する。
- **ユーザー向けメッセージは直書きしない。** Backend では必ず `messages*.properties` のキーを `MessageSource` で解決する。
- **エラーレスポンスの形式は API 仕様に合わせる。** `docs/specs/api-spec.md` の「エラーレスポンス」に定義された JSON 構造（`timestamp`, `status`, `error`, `message`, 必要時 `details`）を守る。

---

## 2. Backend：例外の種類と使い分け

- **業務例外は `RuntimeException` を直接スローしない。** すべて `BusinessException`（`RuntimeException` を継承した業務用基底クラス）またはそのサブクラスで表現する。コード内で `throw new RuntimeException(...)` は書かない。
- **業務例外の基底クラス**は `BusinessException` とする。`ResourceNotFoundException` や `ExternalApiException` は `BusinessException` を継承し、`GlobalExceptionHandler` でサブクラスごとに HTTP ステータスをマッピングする。

| 例外 | 用途 | HTTP にマップ |
|------|------|----------------|
| `BusinessException` | 業務例外の基底クラス（継承元）。直接スローする場合は汎用業務エラーとして扱う | 500 Internal Server Error（既定） |
| `ResourceNotFoundException` | 指定条件でリソースが存在しない（例: ID に該当する Todo なし）。`BusinessException` のサブクラス | 404 Not Found |
| `ExternalApiException` | 外部 API（例: QWen）の呼び出し失敗。`BusinessException` のサブクラス | 502 Bad Gateway |
| `MethodArgumentNotValidException` | Bean Validation（@Valid）違反 | 400 Bad Request |
| `IllegalArgumentException` | 不正な引数・パラメータ | 400 Bad Request |
| `NoResourceFoundException` | 静的リソース未検出（フレームワークがスロー） | 404 Not Found |
| 上記以外の `Exception` | その他すべて | 500 Internal Server Error |

- **Service 層**では、業務上「リソース不在」と判断した場合に `ResourceNotFoundException`、「外部 API 失敗」に `ExternalApiException` をスローする。その他の業務エラーは `BusinessException` またはそのサブクラスを使う。メッセージは `MessageSource` のキーを利用するか、例外のコンストラクタに渡す。
- **新規の業務例外を増やす場合**は、`BusinessException` を継承したクラスを定義し、`GlobalExceptionHandler` にその例外用の `@ExceptionHandler` を追加して、上表と同様に HTTP ステータスとレスポンス形式を揃える。

---

## 3. Backend：GlobalExceptionHandler

- **すべての HTTP エラーはこのハンドラで一元処理する。** Controller や Service で try-catch して ResponseEntity を返さない。
- **各ハンドラの責務**は「例外 → HTTP ステータス + ErrorResponse」への変換のみ。業務ロジックは書かない。

---

## 4. Backend：メッセージキー（messages*.properties）

- **命名**: ドット区切り・camelCase（例: `resource.notFound`, `error.staticResource.notFound`）。
- **追加時**: 同じキーを `messages.properties` と `messages_en.properties` の**両方**に追加する。
- **分類**: 既存の「# --- 〇〇 ---」ブロックに従い、適切なセクションに置く。

---

## 5. Backend：ログ

- ログ出力は **LogHelper** を使用する。`logHelper.error("ESYSXXX0001", args)` のようにログ番号（12 文字）と引数を渡し、文言は messages.properties で解決する。log を渡す必要はなく、ハンドラ・Service に @Slf4j は不要。
- 業務上重要な失敗（リソース不在・バリデーションエラー・外部 API 失敗など）は `logHelper.error("番号", ...)` で記録する。
- 想定内であり、ログがノイズになるだけのケース（例: 静的リソース未検出）は `logHelper.debug("番号", ...)` とする。
- **traceId**（1 リクエスト 1 ID）・**ログ番号**・メッセージ文言の **messages.properties** 対応は [logging.md](logging.md) を参照する。

**GlobalExceptionHandler でのログ例**（例外の logCode を優先し、null 安全にログ）:

```java
@RestControllerAdvice
@RequiredArgsConstructor
public class GlobalExceptionHandler {
    private final MessageSource messageSource;
    private final LogHelper logHelper;

    /** 例外の logCode を優先。未指定時は defaultLogCode。メッセージは null 安全。 */
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

    @ExceptionHandler(ResourceNotFoundException.class)
    public ResponseEntity<ErrorResponse> handleResourceNotFound(ResourceNotFoundException ex, Locale locale) {
        logHandledException("ESYSNOTF0002", ex, false);
        String message = ex.getMessageKey() != null
                ? messageSource.getMessage(ex.getMessageKey(), ex.getMessageArgs(), locale)
                : ex.getMessage();
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(ErrorResponse.builder()
                .timestamp(OffsetDateTime.now().toString())
                .status(HttpStatus.NOT_FOUND.value())
                .error("Not Found")
                .message(message)
                .build());
    }

    @ExceptionHandler(ExternalApiException.class)
    public ResponseEntity<ErrorResponse> handleExternalApi(ExternalApiException ex, Locale locale) {
        logHandledException("ESYSEXTE0001", ex, true);  // 例外付きでスタックトレース出力
        String message = messageSource.getMessage("external.api.failed", new Object[]{ex.getMessage()}, locale);
        return ResponseEntity.status(HttpStatus.BAD_GATEWAY).body(ErrorResponse.builder()
                .timestamp(OffsetDateTime.now().toString())
                .status(HttpStatus.BAD_GATEWAY.value())
                .error("Bad Gateway")
                .message(message)
                .build());
    }
}
```

業務コードでは例外スロー時に **logCode を渡す**（Handler が `ex.getLogCode()` で発生箇所を特定）:

```java
// Service 層でのスロー例
throw new ResourceNotFoundException("Todo", "id", id, "ETODGETO0001");
throw new ExternalApiException(getMessage("external.qwen.communication"), e, "EAIQCOMM0001");
```

---

## 6. Frontend：API エラー

- **API 呼び出し**は `lib/api-client` の `apiRequest` 等を利用し、エラー時は共通の処理に任せる。
- **`response.ok` でない場合**は例外をスローする。エラー文言はレスポンス本文（JSON の `message` 等）を利用し、取得できない場合は `statusText` 等で補う。
- 画面ごとのエラー表示は、この例外（または React Query の error）を利用して行う。

---

## 7. 参照

| 対象 | 参照ドキュメント |
|------|------------------|
| クラス・メソッド名、メッセージキー形式 | `naming-conventions.md` |
| コメント・Javadoc | `comment-checklist.md` |
| ログ（traceId・ログ番号・messages） | `logging.md` |
| エラーレスポンスの JSON 形式 | `docs/specs/api-spec.md`（エラーレスポンス） |
