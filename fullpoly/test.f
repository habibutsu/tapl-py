lambda X. lambda x:X. x;

(lambda X. lambda x:X. x) [All X.X->X];

{*All Y.Y, lambda x:(All Y.Y). x} as {Some X,X->X};

{*Nat, {c=0, f=lambda x:Nat. x}}
  as {Some X, {c:X, f:X->Nat}};

let {X,ops} = {*Nat, {c=0, f=lambda x:Nat. x}}
              as {Some X, {c:X, f:X->Nat}}
in (ops.f ops.c);

{x=true, y=false};
{x=true, y=false}.x;
{true, false};
{true, false}.1;

{X, ops} = {*
    Nat,
    {c=0, f=lambda x:Nat. x}}
as {Some X, {c:X, f:X->Nat}};

(ops.f ops.c);

{*Nat, lambda x:Nat. x} as {Some X, X->Nat};