from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..factory import ASTCacheProtocol


class CSharpTypeInferenceEngine:
    def __init__(self, ast_cache: "ASTCacheProtocol"):
        self.ast_cache = ast_cache
        self._init_known_library_methods()

    def _init_known_library_methods(self):
        self.known_library_methods = {
            "fluentvalidation": {
                "WithMessage",
                "NotEmpty",
                "NotNull",
                "MaximumLength",
                "MinimumLength",
                "Length",
                "Matches",
                "Email",
                "Url",
                "InclusiveBetween",
                "ExclusiveBetween",
                "GreaterThan",
                "GreaterThanOrEqualTo",
                "LessThan",
                "LessThanOrEqualTo",
                "Must",
                "When",
                "Unless",
                "RuleFor",
                "ForMember",
                "TransformFor",
                "SetValidator",
                "Cascade",
                "WithName",
                "WithState",
                "OverridePropertyName",
                "DependentRules",
                "GetDescription",
                "MapFrom",
                "ApplyFilterTo",
                "ApplyAsyncFilterTo",
            },
            "linq": {
                "Select",
                "Where",
                "First",
                "FirstOrDefault",
                "Single",
                "SingleOrDefault",
                "Any",
                "All",
                "Count",
                "LongCount",
                "Sum",
                "Min",
                "Max",
                "Average",
                "Aggregate",
                "OrderBy",
                "OrderByDescending",
                "ThenBy",
                "ThenByDescending",
                "GroupBy",
                "Join",
                "GroupJoin",
                "Take",
                "Skip",
                "TakeWhile",
                "SkipWhile",
                "Distinct",
                "Union",
                "Intersect",
                "Except",
                "ToList",
                "ToArray",
                "ToDictionary",
                "ToLookup",
                "OfType",
                "Cast",
                "AsEnumerable",
                "AsQueryable",
                "Contains",
                "ElementAt",
                "ElementAtOrDefault",
                "Last",
                "LastOrDefault",
                "Append",
                "Prepend",
                "Zip",
            },
            "efcore": {
                "HasColumnName",
                "HasMaxLength",
                "IsRequired",
                "IsUnicode",
                "HasPrecision",
                "HasDefaultValue",
                "HasDefaultValueSql",
                "HasComputedColumnSql",
                "IsRowVersion",
                "IsFixedLength",
                "HasForeignKey",
                "HasPrincipalKey",
                "HasIndex",
                "WithMany",
                "WithOne",
                "HasConstraint",
                "OnDelete",
                "OnUpdate",
                "UseSqlite",
                "UseSqlServer",
                "UseNpgsql",
                "Filter",
                "Eq",
                "Ne",
                "Gt",
                "Ge",
                "Lt",
                "Le",
                "Contains",
                "StartsWith",
                "EndsWith",
                "In",
                "NotIn",
                "Sort",
                "Ascending",
                "Descending",
                "Update",
                "Set",
                "Property",
            },
            "mediatr": {
                "Send",
                "Publish",
                "CreateRequest",
                "CreateRequestHandler",
                "WithRequest",
                "WithBehavior",
            },
            "aspnetcore": {
                "MapGet",
                "MapPost",
                "MapPut",
                "MapDelete",
                "MapGroup",
                "MapControllerRoute",
                "Produces",
                "ProducesProblem",
                "ProducesResponseType",
                "WithName",
                "WithMetadata",
                "AllowAnonymous",
                "Authorize",
                "RequireAuthorization",
                "WithTags",
                "WithGroupName",
                "WithOpenApi",
                "ExcludeFromDescription",
                "Accepts",
            },
            "serialization": {
                "JsonPropertyName",
                "JsonIgnore",
                "JsonProperty",
                "Serialize",
                "Deserialize",
                "ToJson",
                "FromJson",
                "SerializeObject",
                "DeserializeObject",
                "PopulateObject",
                "TryDeserializeObject",
            },
            "logging": {
                "LogInformation",
                "LogWarning",
                "LogError",
                "LogDebug",
                "LogTrace",
                "LogCritical",
                "Log",
            },
            "di": {
                "AddDbContext",
                "AddDbContextPool",
                "AddAuthentication",
                "AddAuthorization",
                "AddControllers",
                "AddRazorPages",
                "AddMvc",
                "AddMvcCore",
                "AddApiControllers",
                "AddGraphQL",
                "AddHostedService",
                "AddScoped",
                "AddTransient",
                "AddSingleton",
                "AddHealthChecks",
                "AddCors",
                "AddSignalR",
                "AddResponseCompression",
                "AddResponseCaching",
                "AddSession",
                "AddDistributedMemoryCache",
                "AddMemoryCache",
                "AddHttpClient",
                "AddHttpClientFactory",
                "AddPolly",
                "AddAutoMapper",
                "AddMediatR",
                "AddFluentValidation",
                "AddValidatorsFromAssemblies",
                "AsImplementedInterfaces",
                "CreateScope",
                "GetService",
                "GetRequiredService",
                "GetServices",
            },
            "efcore_services": {
                "Find",
                "FirstOrDefault",
                "SingleOrDefault",
                "Add",
                "AddAsync",
                "Update",
                "Remove",
                "Attach",
                "Entry",
                "SaveChanges",
                "SaveChangesAsync",
                "ExecuteSqlRaw",
                "ExecuteSqlRawAsync",
                "FromSqlRaw",
                "FromSqlInterpolated",
                "Include",
                "ThenInclude",
                "AsNoTracking",
                "AsTracking",
                "AsQueryable",
                "ToList",
                "ToListAsync",
                "ToArray",
                "ToArrayAsync",
                "BeginTransactionAsync",
                "OpenAsync",
                "CloseAsync",
                "ExecuteAsync",
                "Query",
                "Reload",
                "ReloadAsync",
            },
            "system": {
                "Guid.NewGuid",
                "DateTime.Now",
                "DateTime.UtcNow",
                "DateTime.Today",
                "DateTime.Parse",
                "DateTime.TryParse",
                "TimeSpan.FromDays",
                "TimeSpan.FromHours",
                "TimeSpan.FromMinutes",
                "TimeSpan.FromSeconds",
                "TimeSpan.FromMilliseconds",
                "Environment.NewLine",
                "Environment.GetEnvironmentVariable",
                "Environment.SetEnvironmentVariable",
                "Interlocked.Increment",
                "Interlocked.Decrement",
                "Interlocked.Exchange",
                "Interlocked.CompareExchange",
                "Thread.Sleep",
                "Random.Next",
                "Random.NextDouble",
                "Math.Round",
                "Math.Floor",
                "Math.Ceiling",
                "Math.Truncate",
                "Math.Abs",
                "Math.Max",
                "Math.Min",
                "String.IsNullOrEmpty",
                "String.IsNullOrWhiteSpace",
                "String.Format",
                "String.Concat",
                "String.Join",
                "String.Equals",
                "String.Compare",
                "String.CompareTo",
                "String.Copy",
                "String.Intern",
                "String.IsInterned",
                "Object.Equals",
                "Object.ReferenceEquals",
                "Object.Init",
                "Activator.CreateInstance",
                "GetValue",
                "GetValueOrDefault",
            },
            "operators": {
                "nameof",
                "sizeof",
                "typeof",
                "stackalloc",
                "checked",
                "unchecked",
                "default",
                "new",
            },
            "async": {
                "Task.Run",
                "Task.FromResult",
                "Task.FromException",
                "Task.Delay",
                "Task.Wait",
                "Task.WhenAll",
                "Task.WhenAny",
                "Task.ContinueWith",
                "Task.Factory.StartNew",
                "ValueTask",
                "ValueTask.FromResult",
            },
            "linq_extensions": {
                "DistinctBy",
                "UnionBy",
                "IntersectBy",
                "ExceptBy",
                "Join",
                "GroupJoin",
                "Zip",
                "Chunk",
                "TryGetNonEnumeratedCount",
                "Index",
                "FirstOrDefaultAsync",
                "ToListAsync",
                "ToArrayAsync",
                "SingleOrDefaultAsync",
                "CountAsync",
                "AnyAsync",
                "AllAsync",
                "SumAsync",
                "AverageAsync",
                "MinAsync",
                "MaxAsync",
            },
        }
        self.all_known_methods = set()
        for methods in self.known_library_methods.values():
            self.all_known_methods.update(methods)

    def infer_type(self, node, caller_node=None, caller_qn=None):
        if node is None:
            return None
        node_type = node.type if hasattr(node, "type") else str(type(node))
        if node_type == "member_expression":
            member_name = node.text.decode() if hasattr(node, "text") else str(node)
            if caller_qn:
                return self._infer_from_member_access(member_name, caller_qn)
        return None

    def _infer_from_member_access(self, member_name: str, caller_qn: str):
        base_name = member_name.split("<")[0] if "<" in member_name else member_name
        if base_name in self.all_known_methods:
            for library, methods in self.known_library_methods.items():
                if base_name in methods:
                    return f"csharp.library.{library}.{base_name}"
        return None

    def is_known_library_method(self, method_name: str) -> bool:
        return method_name in self.all_known_methods

    def get_library_method_type(self, method_name: str) -> str | None:
        if method_name not in self.all_known_methods:
            return None
        for library, methods in self.known_library_methods.items():
            if method_name in methods:
                return library
        return None

    def resolve_method_chain(self, call_name: str, caller_qn: str) -> str | None:
        if "." not in call_name:
            method_name = call_name.split("<")[0] if "<" in call_name else call_name
            if method_name in self.all_known_methods:
                library = self.get_library_method_type(method_name)
                if library:
                    return f"csharp.stdlib.{library}.{method_name}"
            return None
        parts = call_name.split(".")
        method_name = parts[-1]
        base_name = method_name.split("<")[0] if "<" in method_name else method_name
        if base_name in self.all_known_methods:
            library = self.get_library_method_type(base_name)
            if library:
                return f"csharp.stdlib.{library}.{base_name}"
        return None

    def resolve_linq_expression(self, call_name: str) -> str | None:
        linq_keywords = {
            "where",
            "select",
            "any",
            "all",
            "first",
            "firstordefault",
            "single",
            "singleordefault",
            "count",
            "sum",
            "min",
            "max",
            "average",
            "aggregate",
            "orderby",
            "orderbydescending",
            "thenby",
            "thenbydescending",
            "groupby",
            "take",
            "skip",
            "distinct",
            "union",
            "tolist",
            "toarray",
        }
        lower_name = call_name.lower()
        for keyword in linq_keywords:
            if keyword in lower_name:
                # (H) Return without "StdlibMethod." prefix - caller adds it
                return f"csharp.stdlib.Linq.{keyword.title()}"
        return None

    def resolve_property_access(self, property_name: str, caller_qn: str) -> str | None:
        if caller_qn and "." in caller_qn:
            return f"Property.{caller_qn}.{property_name}"
        return f"Property.{property_name}"

    def resolve_indexer_access(
        self, index_expression: str, caller_qn: str
    ) -> str | None:
        return f"Indexer.{caller_qn}[]"

    def resolve_async_call(self, call_name: str) -> str | None:
        async_keywords = [
            "Task.Run",
            "Task.FromResult",
            "Task.Delay",
            "ExecuteAsync",
            "SendAsync",
            "PublishAsync",
            "GetAsync",
            "PostAsync",
            "PutAsync",
            "DeleteAsync",
        ]
        for keyword in async_keywords:
            if keyword.lower() in call_name.lower():
                return f"csharp.stdlib.Async.{keyword}"
        return None

    def resolve_operator(self, call_name: str) -> str | None:
        if call_name in self.known_library_methods.get("operators", set()):
            return f"csharp.stdlib.Operator.{call_name}"
        if call_name.startswith("Guid."):
            return "csharp.stdlib.System.Guid.NewGuid"
        if call_name.startswith("DateTime."):
            if "Now" in call_name:
                return "csharp.stdlib.System.DateTime.Now"
            if "UtcNow" in call_name:
                return "csharp.stdlib.System.DateTime.UtcNow"
            if "Today" in call_name:
                return "csharp.stdlib.System.DateTime.Today"
            return "csharp.stdlib.System.DateTime"
        if call_name.startswith("TimeSpan."):
            if "From" in call_name:
                return f"csharp.stdlib.System.TimeSpan.{call_name.split('.')[-1]}"
            return "csharp.stdlib.System.TimeSpan"
        if call_name.startswith("Environment."):
            return f"csharp.stdlib.System.Environment.{call_name.split('.')[-1]}"
        if call_name.startswith("Interlocked."):
            return (
                f"csharp.stdlib.System.Threading.Interlocked.{call_name.split('.')[-1]}"
            )
        if call_name.startswith("Thread."):
            return f"csharp.stdlib.System.Threading.{call_name}"
        if call_name.startswith("Random."):
            return "csharp.stdlib.System.Random"
        if call_name.startswith("Math."):
            return f"csharp.stdlib.System.Math.{call_name.split('.')[-1]}"
        if call_name.startswith("String."):
            return f"csharp.stdlib.System.String.{call_name.split('.')[-1]}"
        if call_name.startswith("Object."):
            return f"csharp.stdlib.System.Object.{call_name.split('.')[-1]}"
        if call_name.startswith("Activator."):
            return f"csharp.stdlib.System.Activator.{call_name.split('.')[-1]}"
        if call_name.startswith("Assembly."):
            return (
                f"csharp.stdlib.System.Reflection.Assembly.{call_name.split('.')[-1]}"
            )
        if call_name.startswith("Type."):
            return f"csharp.stdlib.System.Type.{call_name.split('.')[-1]}"
        if call_name.startswith("MethodInfo."):
            return "csharp.stdlib.System.Reflection.MethodInfo"
        if call_name.startswith("WebApplication."):
            return f"csharp.stdlib.AspNetCore.WebApplication.{call_name.split('.')[-1]}"
        return None

    def resolve_di_extension(self, call_name: str) -> str | None:
        if call_name in self.known_library_methods.get("di", set()):
            return f"csharp.stdlib.DependencyInjection.{call_name}"
        if call_name in self.known_library_methods.get("efcore_services", set()):
            return f"csharp.stdlib.EntityFrameworkCore.{call_name}"
        if call_name in self.known_library_methods.get("async", set()):
            return f"csharp.stdlib.{call_name}"
        return None

    def resolve_generic_call(self, call_name: str) -> str | None:
        generic_patterns = {
            "AddExceptionHandler": "csharp.stdlib.DependencyInjection.IHostBuilder.AddExceptionHandler",
            "AddExceptionHandler<T>": "csharp.stdlib.DependencyInjection.IHostBuilder.AddExceptionHandler",
            "RuleFor": "csharp.library.fluentvalidation.RuleFor",
            "RuleFor<T>": "csharp.library.fluentvalidation.RuleFor",
            "RuleFor<T, TProperty>": "csharp.library.fluentvalidation.RuleFor",
            "ForMember": "csharp.library.fluentvalidation.ForMember",
            "TransformFor": "csharp.library.fluentvalidation.TransformFor",
            "AddDbContext": "csharp.stdlib.DependencyInjection.AddDbContext",
            "AddDbContext<TContext>": "csharp.stdlib.DependencyInjection.AddDbContext",
            "AddDbContext<TContext, TOptions>": "csharp.stdlib.DependencyInjection.AddDbContext",
            "AddScoped": "csharp.stdlib.DependencyInjection.AddScoped",
            "AddScoped<TService>": "csharp.stdlib.DependencyInjection.AddScoped",
            "AddScoped<TService, TImplementation>": "csharp.stdlib.DependencyInjection.AddScoped",
            "AddTransient": "csharp.stdlib.DependencyInjection.AddTransient",
            "AddTransient<TService>": "csharp.stdlib.DependencyInjection.AddTransient",
            "AddTransient<TService, TImplementation>": "csharp.stdlib.DependencyInjection.AddTransient",
            "AddSingleton": "csharp.stdlib.DependencyInjection.AddSingleton",
            "AddSingleton<TService>": "csharp.stdlib.DependencyInjection.AddSingleton",
            "AddSingleton<TService, TImplementation>": "csharp.stdlib.DependencyInjection.AddSingleton",
            "AddAuthentication": "csharp.stdlib.DependencyInjection.AddAuthentication",
            "AddAuthorization": "csharp.stdlib.DependencyInjection.AddAuthorization",
            "AddHealthChecks": "csharp.stdlib.DependencyInjection.AddHealthChecks",
            "AddMediatR": "csharp.stdlib.DependencyInjection.AddMediatR",
            "AddFluentValidation": "csharp.stdlib.DependencyInjection.AddFluentValidation",
            "AddAutoMapper": "csharp.stdlib.DependencyInjection.AddAutoMapper",
            "AddCors": "csharp.stdlib.DependencyInjection.AddCors",
            "Configure": "csharp.stdlib.DependencyInjection.Configure",
            "Configure<TOptions>": "csharp.stdlib.DependencyInjection.Configure",
            "GetRequiredService": "csharp.stdlib.DependencyInjection.ServiceProvider.GetRequiredService",
            "GetService": "csharp.stdlib.DependencyInjection.ServiceProvider.GetService",
        }
        base_name = call_name.split("<")[0]
        if base_name in generic_patterns:
            return generic_patterns[base_name]
        return None

    def resolve_constructor_call(self, call_name: str) -> str | None:
        if call_name.startswith("new "):
            class_name = call_name[4:].split("(")[0].strip()
            if class_name.endswith("Exception"):
                return f"csharp.stdlib.System.{class_name}"
            if class_name.endswith("Attribute"):
                return f"csharp.stdlib.System.Attribute.{class_name}"
            if "." in class_name:
                parts = class_name.rsplit(".", 1)
                return f"csharp.stdlib.{parts[0]}.{parts[1]}"
            return f"csharp.stdlib.UserDefined.{class_name}"
        return None

    def resolve_known_property_access(self, call_name: str) -> str | None:
        if call_name.startswith("httpContext."):
            return "csharp.stdlib.AspNetCore.HttpContext"
        if call_name.startswith("User."):
            return "csharp.stdlib.AspNetCore.ClaimsPrincipal"
        if ".session." in call_name or call_name.startswith("session."):
            return "csharp.stdlib.EntityFrameworkCore.DbContext"
        if ".unitOfWork." in call_name or call_name.startswith("unitOfWork."):
            return "csharp.library.EntityFramework.UnitOfWork"
        if ".logger." in call_name or call_name.startswith("logger."):
            return "csharp.stdlib.Logging.ILogger"
        if ".configuration." in call_name or call_name.startswith("configuration."):
            return "csharp.stdlib.Configuration.IConfiguration"
        if ".transaction." in call_name or call_name.startswith("transaction."):
            return "csharp.stdlib.EntityFrameworkCore.DatabaseTransaction"
        return None

    def is_indexer_access(self, call_name: str) -> bool:
        return "[" in call_name and "]" in call_name

    def is_async_call(self, call_name: str) -> bool:
        async_indicators = ["async", "await", "Task", "Promise"]
        return any(
            indicator.lower() in call_name.lower() for indicator in async_indicators
        )

    def resolve_builder_pattern(self, call_name: str) -> str | None:
        if call_name.endswith(".Build") or call_name.endswith(".BuildAsync"):
            return "csharp.stdlib.DependencyInjection.IHostBuilder.Build"
        if call_name.endswith(".Services"):
            return "csharp.stdlib.DependencyInjection.IServiceCollection"
        if ".Add" in call_name and "services" in call_name.lower():
            return "csharp.stdlib.DependencyInjection.IServiceCollection.Add"
        if ".AddJsonFile" in call_name or ".AddEnvironmentVariables" in call_name:
            return "csharp.stdlib.Configuration.ConfigurationBuilder"
        if "BuildServiceProvider" in call_name:
            return "csharp.stdlib.DependencyInjection.IServiceProvider"
        return None

    def resolve_actor_pattern(self, call_name: str) -> str | None:
        if ".Actor" in call_name:
            return "csharp.library.Dapr.Actor.Actor"
        if "Actor." in call_name:
            return "csharp.library.Dapr.Actor"
        return None
