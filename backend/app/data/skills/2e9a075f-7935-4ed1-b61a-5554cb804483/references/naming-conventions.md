# バックエンド命名規約

MinutesTrace プロジェクトの Java と Spring Boot バックエンドコードの完全な命名規則。

## パッケージ・クラス

| パッケージ | クラス名規則 | 例 |
|------------|--------------|-----|
| `controller` | `XxxController`（**Xxx = リソース名** または **機能名**） | リソース: `MeetingController`, `TodoController` / 機能: `AiController` |
| `dto` | Request: `XxxRequest` / Response: `XxxResponse` / 要素: `XxxCandidate`（Xxx = リソース or 機能） | `TodoRequest`, `MeetingResponse`, `TodoCandidate` |
| `entity` | **単数形のリソース名 + `Entity`**（Xxx = テーブルに対応する名詞） | `TodoEntity`, `MeetingEntity` |
| `service` | `XxxService`（Xxx = リソース名 または 外部サービス名） | `TodoService`, `QWenService` |
| `mapper` | `XxxMapper`（**Xxx = リソース名**。1 テーブル = 1 Mapper） | `TodoMapper`, `MeetingMapper` |
| `config` | `XxxConfig` | `CorsConfig`, `MessageConfig` |
| `exception` | `XxxException` / `XxxHandler` | `ResourceNotFoundException`, `GlobalExceptionHandler` |

### Xxx の取り方

- **リソース**（会議・Todo など）を扱うなら**リソース名の単数形**（Meeting, Todo）
- **特定機能**だけの API なら**機能名**（Ai）
- Mapper/Entity は必ず**リソース名**

## メソッド・変数

- **camelCase**を使用
- 定数は **UPPER_SNAKE_CASE**

### メソッド名の接頭辞

- 取得：`getXxx` / `findXxx`
- 作成：`createXxx`
- 更新：`updateXxx`
- 削除：`deleteXxx`
- 変換：`convertToXxx`

### 例

```java
// ✅ 良い例
public TodoResponse getTodo(String id) { }
public List<TodoEntity> findByMeetingId(String meetingId) { }
public TodoResponse createTodo(TodoRequest request) { }
public TodoResponse updateTodo(String id, TodoRequest request) { }
public void deleteTodo(String id) { }
public TodoResponse convertToResponse(TodoEntity entity) { }

// 定数
private static final int MAX_RETRY_COUNT = 3;
private static final String DEFAULT_PRIORITY = "medium";
```

## API パス

- ベース：`/api`
- リソースは**複数形・小文字**

### 例

```
/api/meetings
/api/meetings/{id}
/api/meetings/{meetingId}/todos
/api/todos
/api/todos/{id}
/api/ai/generate-todos
/api/me/todos
```

## MyBatis XML

### ファイル名

- `XxxMapper.xml`（例：`TodoMapper.xml`、`MeetingMapper.xml`）

### ResultMap ID

- `XxxResultMap`（例：`TodoResultMap`、`MeetingResultMap`）

### SQL 文 ID

- **camelCase**（Java メソッド名と一致）
- 例：`findById`、`findByMeetingId`、`insert`、`update`、`delete`

### 例

```xml
<mapper namespace="com.meetingtracker.mapper.TodoMapper">
    <resultMap id="TodoResultMap" type="com.meetingtracker.entity.TodoEntity">
        <id column="id" property="id"/>
        <result column="meeting_id" property="meetingId"/>
        <!-- ... -->
    </resultMap>

    <select id="findById" resultMap="TodoResultMap">
        SELECT id, meeting_id, title, description
        FROM todos
        WHERE id = #{id}
    </select>
</mapper>
```

### 重要

- **SQL は XML にのみ記述**（Java インターフェースにアノテーションで SQL を書かない）

## メッセージキー（messages.properties）

- **ドット区切り・camelCase**

### 例

```properties
# リソース関連
resource.notFound=指定されたリソースが見つかりません

# バリデーション関連
validation.title.required=タイトルは必須です
validation.date.required=日付は必須です
validation.priority.pattern=優先度は low, medium, high のいずれかを指定してください

# エラー関連
error.staticResource.notFound=静的リソースが見つかりません
error.externalApi.failed=外部APIの呼び出しに失敗しました
```

## 一般的なパターン

### Controller

```java
@RestController
@RequestMapping("/api/todos")
@RequiredArgsConstructor
public class TodoController {
    private final TodoService todoService;

    @GetMapping
    public ResponseEntity<List<TodoResponse>> getTodos() {
        return ResponseEntity.ok(todoService.getTodos());
    }

    @PostMapping
    public ResponseEntity<TodoResponse> createTodo(@Valid @RequestBody TodoRequest request) {
        TodoResponse response = todoService.createTodo(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }
}
```

### Service

```java
@Service
@Transactional
@RequiredArgsConstructor
public class TodoService {
    private final TodoMapper todoMapper;

    public TodoResponse createTodo(TodoRequest request) {
        // メソッドの入退場ログは AOP（LoggingAspect）が出力。例外スロー時は logCode を渡す（logging.md 参照）
        TodoEntity entity = convertToEntity(request);
        todoMapper.insert(entity);
        return convertToResponse(entity);
    }

    public TodoResponse getTodoById(String id) {
        TodoEntity todo = todoMapper.findById(id);
        if (todo == null) {
            throw new ResourceNotFoundException("Todo", "id", id, "ETODGETO0001");
        }
        return convertToResponse(todo);
    }

    private TodoEntity convertToEntity(TodoRequest request) {
        // 変換ロジック
    }

    private TodoResponse convertToResponse(TodoEntity entity) {
        // 変換ロジック
    }
}
```

### DTO

```java
@Data
@NoArgsConstructor
@AllArgsConstructor
public class TodoRequest {
    @NotBlank(message = "{validation.meetingId.required}")
    private String meetingId;

    @NotBlank(message = "{validation.title.required}")
    private String title;

    private String description;

    @Pattern(regexp = "low|medium|high", message = "{validation.priority.pattern}")
    private String priority;
}
```

### Entity

```java
@Data
@NoArgsConstructor
@AllArgsConstructor
public class TodoEntity {
    /** Todo ID */
    private String id;

    /** 会議 ID */
    private String meetingId;

    /** タイトル */
    private String title;

    /** 説明 */
    private String description;

    /** 担当者 */
    private String assignee;

    /** 期限 */
    private String dueDate;

    /** 優先度: low/medium/high */
    private String priority;

    /** ステータス: pending/in_progress/completed */
    private String status;

    /** 作成者 */
    private String createdBy;

    /** 作成日時 */
    private String createdAt;

    /** 更新日時 */
    private String updatedAt;

    /** AI生成フラグ */
    private Boolean aiGenerated;
}
```

## レビューチェックリスト

コードレビュー時に確認：

- [ ] パッケージ名が小文字
- [ ] クラス名が PascalCase で適切な接尾辞（Controller、Service、Mapper、Request、Response、Entity）
- [ ] メソッド名・変数名が camelCase
- [ ] 定数が UPPER_SNAKE_CASE
- [ ] API パスがベース `/api` + 複数形リソース
- [ ] MyBatis XML のファイル名・ResultMap ID・SQL 文 ID が規約に準拠
- [ ] メッセージキーがドット区切り・camelCase
- [ ] メソッド名の接頭辞が適切（get/find/create/update/delete/convert）
