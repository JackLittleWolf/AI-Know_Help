# DTOバリデーションルール

## 適用対象
- すべてのリクエストDTO（`*Request.java`）
- すべてのレスポンスDTO（`*Response.java`）

## ルール

### 1. リクエストDTOには適切なバリデーションアノテーションを使用する

**必須項目**:
```java
@NotBlank(message = "{validation.fieldName.required}")
private String fieldName;

@NotNull(message = "{validation.fieldName.required}")
private Integer fieldName;
```

**パターン検証**:
```java
@Pattern(regexp = "pattern", message = "{validation.fieldName.pattern}")
private String fieldName;
```

**例**:
```java
@Data
@NoArgsConstructor
@AllArgsConstructor
public class TodoRequest {
    @NotBlank(message = "{validation.meetingId.required}")
    private String meetingId;
    
    @NotBlank(message = "{validation.title.required}")
    private String title;
    
    @Pattern(regexp = "low|medium|high", message = "{validation.priority.pattern}")
    private String priority;
}
```

### 2. DTOにデフォルト値を設定しない

**❌ NG**:
```java
private String priority = "medium";
private String status = "pending";
```

**✅ OK**:
```java
// DTOではnullを許容
private String priority;
private String status;

// Service層でデフォルト値を設定
todo.setPriority(request.getPriority() != null ? request.getPriority() : "medium");
```

**理由**:
- nullと空文字列の区別が可能
- Optionalフィールドの扱いが明確
- ビジネスロジックの責任がService層に集約

### 3. バリデーションメッセージは多言語対応する

**messages.properties**:
```properties
validation.meetingId.required=会議IDは必須です
validation.title.required=タイトルは必須です
```

**messages_en.properties**:
```properties
validation.meetingId.required=Meeting ID is required
validation.title.required=Title is required
```

### 4. レスポンスDTOにはエラーフィールドを含める

```java
@Data
@NoArgsConstructor
@AllArgsConstructor
public class ApiResponse {
    private List<DataItem> data;
    private String error;  // エラー時に使用
    
    // エラー専用コンストラクタ
    public ApiResponse(String error) {
        this.data = List.of();
        this.error = error;
    }
}
```

## チェックリスト

- [ ] すべての必須フィールドに`@NotBlank`または`@NotNull`がある
- [ ] パターン検証が必要なフィールドに`@Pattern`がある
- [ ] バリデーションメッセージが多言語対応されている
- [ ] DTOにデフォルト値が設定されていない
- [ ] レスポンスDTOにエラーフィールドがある
